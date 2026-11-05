"""Reference multi-instance Redis admission guard for M3 qualification only.

Security boundary: source is supplied by the host from ASGI connection metadata,
never from Forwarded/X-Forwarded-For or a JSON claim. Redis EVAL atomically
applies all quotas. This is a *fixed-window since first attempt* limiter, not
a universal bot detector, CAPTCHA, credential stuffing defense or global SLO.
"""

import contextvars
import hashlib
import hmac

from redis.asyncio import Redis

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId

HOST_SOURCE: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "pyauthkit_m3_host_source", default=None
)

_ATOMIC_LIMITS = """
local allowed = 1
for i = 1, #KEYS do
    local count = redis.call('INCR', KEYS[i])
    if count == 1 then
        redis.call('EXPIRE', KEYS[i], tonumber(ARGV[1]))
    end
    if count > tonumber(ARGV[i + 1]) then
        allowed = 0
    end
end
return allowed
"""


class RedisPasswordAttemptGuard:
    """Shared counter buckets scoped by approved tenant + peer + identity.

    [Ports & Adapters] [SECURITY: fail closed] [DIP: host owns admission]
    A broken Redis connection raises; PasswordAuthenticator maps to AuthError.
    """

    def __init__(
        self,
        *,
        redis: Redis,
        hmac_key: bytes,
        window_seconds: int = 60,
        max_per_source: int = 12,
        max_per_identity: int = 12,
    ) -> None:
        if not isinstance(hmac_key, bytes) or len(hmac_key) < 32:
            raise ValueError("ephemeral host HMAC key must have >=32 random bytes")
        if not all(
            type(value) is int and value > 0
            for value in (window_seconds, max_per_source, max_per_identity)
        ):
            raise ValueError("positive quotas and window required")
        self._redis = redis
        self._key = hmac_key
        self._ttl = window_seconds
        self._source_limit = max_per_source
        self._identity_limit = max_per_identity

    def _digest(self, *components: str) -> str:
        # Length prefixes avoid concatenation ambiguity between scope/source.
        message = b"".join(
            len(piece.encode("utf-8")).to_bytes(4, "big") + piece.encode("utf-8")
            for piece in components
        )
        return hmac.new(self._key, message, hashlib.sha256).hexdigest()

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        identifier_kind: str | None,
        identifier_value: str | None,
    ) -> bool:
        source = HOST_SOURCE.get()
        if not isinstance(source, str) or not source:
            return False
        if not isinstance(scope_ref, TrustedScopeRef):
            return False
        # Source and identifier are separately limited across all app replicas.
        peer_key = "m3q:src:" + self._digest(scope_ref.value, source)
        account_key = "m3q:acct:" + self._digest(
            scope_ref.value, identifier_kind or "unknown", identifier_value or "unknown"  # pragma: allowlist secret
        )
        decision = await self._redis.eval(
            _ATOMIC_LIMITS,
            2,
            peer_key,
            account_key,
            self._ttl,
            self._source_limit,
            self._identity_limit,
        )
        return decision == 1
