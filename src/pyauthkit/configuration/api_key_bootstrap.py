"""M6 trusted composition route for an M4 API Key secret consumer.

The user-facing generic bootstrap deliberately refuses snapshots with secrets.
This specialized function validates every referenced HMAC key before admitting
one API-key authenticator to the ordinary M2 engine registry.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping

from pyauthkit.adapters.api_key_authenticator import ApiKeyAuthenticator
from pyauthkit.adapters.api_key_secret import ScopedApiKeySecretSource
from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.application.policy import FinalRule
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.temporal import Clock
from pyauthkit.ports.api_key import ApiKeyCredentialResolver
from pyauthkit.ports.api_key_guard import ApiKeyAttemptGuard
from pyauthkit.ports.authenticator import Authenticator
from pyauthkit.ports.events import AuthenticationEventSink
from pyauthkit.ports.secrets import SecretResolver

from .bootstrap import M6Runtime, _compose_approved_runtime
from .models import ConfigurationRejected, ConfigurationSnapshot
from .secrets import SecretAccessPolicy


async def compose_secret_backed_api_key_runtime(
    snapshot: ConfigurationSnapshot,
    *,
    bindings: Mapping[tuple[TrustedScopeRef, str], SecretRef],
    access_policy: SecretAccessPolicy,
    secret_resolver: SecretResolver,
    credential_resolver: ApiKeyCredentialResolver,
    attempt_guard: ApiKeyAttemptGuard,
    other_authenticators: Iterable[Authenticator] = (),
    final_rule: FinalRule | None = None,
    clock: Clock | None = None,
    event_sink: AuthenticationEventSink | None = None,
    minimum_generation: int = 1,
) -> M6Runtime:
    """Build an M6 runtime only after the M4 secret consumer is truly wired.

    The purpose of the async preflight is bootstrap availability, not a
    guarantee of secret availability for later authentication attempts.
    """
    if not isinstance(snapshot, ConfigurationSnapshot):
        raise ConfigurationRejected("invalid configuration snapshot")
    if type(minimum_generation) is not int or minimum_generation < 1:
        raise ConfigurationRejected("invalid generation floor")
    if snapshot.generation.value < minimum_generation:
        raise ConfigurationRejected("configuration generation is stale")
    try:
        key_source = ScopedApiKeySecretSource(
            snapshot=snapshot,
            access_policy=access_policy,
            resolver=secret_resolver,
            bindings=bindings,
        )
        await key_source.preflight()
        proof = HmacApiKeyVerifier(
            key_source=key_source,
            approved_refs=key_source.approved_refs,
        )
        api_key_authenticator = ApiKeyAuthenticator(
            resolver=credential_resolver,
            proof_verifier=proof,
            attempt_guard=attempt_guard,
            clock=clock,
        )
        candidates = [api_key_authenticator, *other_authenticators]
        if any(auth.method is EvidenceMethod.API_KEY for auth in candidates[1:]):
            raise ConfigurationRejected("duplicate API key secret consumer")
        return _compose_approved_runtime(
            snapshot,
            authenticators=candidates,
            final_rule=final_rule,
            event_sink=event_sink,
            minimum_generation=minimum_generation,
            admitted_secret_refs=frozenset(snapshot.secret_refs),
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        # No provider error text or secret material survives composition failure.
        raise ConfigurationRejected("API key secret bootstrap rejected") from None
