"""Strict secret access gate. No implicit provider, cache or environment fallback."""

import asyncio
import math
from dataclasses import dataclass

from pyauthkit.domain.secret import SecretRef
from pyauthkit.ports.secrets import SecretResolver

from .models import ConfigurationSnapshot


class SecretResolutionUnavailable(Exception):
    """Sanitized failure; the provider's exception may contain secret bytes."""


@dataclass(frozen=True, slots=True, repr=False)
class SecretGrant:
    provider: str
    namespace: str
    purpose: str

    def __post_init__(self) -> None:
        # Reuse VO validation to keep provider/scope/purpose grammar identical.
        try:
            SecretRef(self.provider, self.namespace, "probe", "v1", self.purpose)
        except ValueError:
            raise ValueError("invalid secret grant") from None

    def __repr__(self) -> str:
        return "SecretGrant(<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class SecretAccessPolicy:
    allowed: frozenset[SecretGrant]

    def __post_init__(self) -> None:
        if not isinstance(self.allowed, frozenset) or not all(
            isinstance(grant, SecretGrant) for grant in self.allowed
        ):
            raise ValueError("invalid secret access policy")

    def __repr__(self) -> str:
        return "SecretAccessPolicy(<host-approved>)"


async def resolve_authorized_secret(
    *,
    snapshot: ConfigurationSnapshot,
    policy: SecretAccessPolicy,
    resolver: SecretResolver,
    ref: SecretRef,
    purpose: str,
    timeout_seconds: float = 3.0,
) -> bytes:
    """Deliver bytes to an approved caller, without leaking provider exceptions.

    The caller is a trusted bootstrap consumer, not an HTTP client. Python
    bytes cannot be guaranteed to be zeroized; consumers must bound retention.
    """
    if (
        not isinstance(snapshot, ConfigurationSnapshot)
        or not isinstance(policy, SecretAccessPolicy)
        or not isinstance(ref, SecretRef)
        or ref not in snapshot.secret_refs
        or ref.purpose != purpose
        or SecretGrant(ref.provider, ref.namespace, purpose) not in policy.allowed
    ):
        raise SecretResolutionUnavailable("secret access denied")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (float, int))
        or not math.isfinite(timeout_seconds)
        or not 0 < timeout_seconds <= 30
    ):
        raise SecretResolutionUnavailable("invalid secret timeout")
    try:
        async with asyncio.timeout(timeout_seconds):
            material = await resolver.resolve(ref=ref, purpose=purpose)
        if type(material) is not bytes or not material:
            raise SecretResolutionUnavailable("secret unavailable")
        return material
    except asyncio.CancelledError:
        raise
    except Exception:
        # Do not preserve a chained exception with a provider's secret-bearing str.
        raise SecretResolutionUnavailable("secret unavailable") from None
