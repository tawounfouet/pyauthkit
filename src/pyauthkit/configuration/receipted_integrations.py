"""Experimental M6 receipted adapters for the actual M4 and M5 consumers.

[ARCH: Application Service] [SECURITY: Explicit Composition]
The ordinary M4 and M5 trusted composers remain the only verification
authority. The receipt gateway wraps their resulting exact-generation M2
engine with no best-effort audit sink. No second verifier is implemented.

These factories DO NOT enable audit_delivery=required and cannot prevent a
privileged host from invoking a separately constructed M2 engine. Exclusivity
must be implemented and independently reviewed at the framework boundary.
"""

from __future__ import annotations

from collections.abc import Mapping

from pyauthkit.adapters.audit_required_sqlite import SqliteRequiredAuditCommitter
from pyauthkit.application.policy import FinalRule
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.temporal import Clock
from pyauthkit.ports.api_key import ApiKeyCredentialResolver
from pyauthkit.ports.api_key_guard import ApiKeyAttemptGuard
from pyauthkit.ports.secrets import SecretResolver

from .api_key_bootstrap import compose_secret_backed_api_key_runtime
from .jwt_bootstrap import EgressGrants, compose_trusted_jwt_runtime
from .models import ConfigurationRejected, ConfigurationSnapshot
from .receipted_audit import ReceiptedDecisionGateway
from .secrets import SecretAccessPolicy


def _validate_audited_composition(
    snapshot: ConfigurationSnapshot,
    committer: SqliteRequiredAuditCommitter,
) -> None:
    if not isinstance(snapshot, ConfigurationSnapshot):
        raise ConfigurationRejected("invalid receipted runtime snapshot")
    if type(committer) is not SqliteRequiredAuditCommitter:
        raise ConfigurationRejected("unapproved auditable commit store")
    if snapshot.audit_delivery.mode != "best_effort":
        # Required delivery is not a public policy option yet.
        raise ConfigurationRejected("unsupported audit policy")


async def compose_receipted_api_key_gateway(
    snapshot: ConfigurationSnapshot,
    *,
    bindings: Mapping[tuple[TrustedScopeRef, str], SecretRef],
    access_policy: SecretAccessPolicy,
    secret_resolver: SecretResolver,
    credential_resolver: ApiKeyCredentialResolver,
    attempt_guard: ApiKeyAttemptGuard,
    committer: SqliteRequiredAuditCommitter,
    final_rule: FinalRule | None = None,
    clock: Clock | None = None,
    minimum_generation: int = 1,
) -> ReceiptedDecisionGateway:
    """M4 HMAC -> M2 final policy -> local commit -> return.

    Only an API_KEY-only host snapshot is admitted by this candidate.
    The existing M4 secret-ref preflight is preserved unchanged, but the
    runtime is not handed to the host except inside the gateway.
    """
    _validate_audited_composition(snapshot, committer)
    if (
        snapshot.schema_version != 1
        or not snapshot.secret_refs
        or snapshot.jwt_profiles
        or any(
            binding.allowed_methods != frozenset({EvidenceMethod.API_KEY})
            for binding in snapshot.bindings
        )
    ):
        raise ConfigurationRejected("receipted API key scope not admitted")
    runtime = await compose_secret_backed_api_key_runtime(
        snapshot,
        bindings=bindings,
        access_policy=access_policy,
        secret_resolver=secret_resolver,
        credential_resolver=credential_resolver,
        attempt_guard=attempt_guard,
        final_rule=final_rule,
        clock=clock,
        event_sink=None,
        minimum_generation=minimum_generation,
    )
    if runtime.snapshot is not snapshot:
        raise ConfigurationRejected("receipted API key generation mismatch")
    return ReceiptedDecisionGateway(base=runtime, committer=committer)


def compose_receipted_jwt_gateway(
    snapshot: ConfigurationSnapshot,
    *,
    approved_static_keysets: Mapping[str, tuple[str, ...]],
    committer: SqliteRequiredAuditCommitter,
    approved_jwks_egress: EgressGrants | None = None,
    final_rule: FinalRule | None = None,
    clock: Clock | None = None,
    minimum_generation: int = 1,
) -> ReceiptedDecisionGateway:
    """M5 RS256 verified JWT -> M2 policy -> local commit -> return.

    No token-selected authority or additional authenticator is admitted.
    Trust profiles/egress are validated by the original M5 composer.
    """
    _validate_audited_composition(snapshot, committer)
    if (
        snapshot.schema_version != 2
        or not snapshot.jwt_profiles
        or snapshot.secret_refs
        or any(
            binding.allowed_methods != frozenset({EvidenceMethod.JWT})
            for binding in snapshot.bindings
        )
    ):
        raise ConfigurationRejected("receipted JWT scope not admitted")
    runtime = compose_trusted_jwt_runtime(
        snapshot,
        approved_static_keysets=approved_static_keysets,
        approved_jwks_egress=approved_jwks_egress,
        final_rule=final_rule,
        clock=clock,
        event_sink=None,
        minimum_generation=minimum_generation,
    )
    if runtime.snapshot is not snapshot:
        raise ConfigurationRejected("receipted JWT generation mismatch")
    return ReceiptedDecisionGateway(base=runtime, committer=committer)
