"""Redis-backed shared M4 API-key admission, test-host only.

Atomic Lua applies scope, peer and selector quotas. Host ASGI socket peer is
trusted *only* for this no-proxy loopback fixture, never from forwarded headers.
"""

import contextvars
import hashlib
import hmac

from redis.asyncio import Redis

from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId

HOST_PEER: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "m4_qualification_socket_peer", default=None
)

_LUA = """
local ok = 1
for i = 1, #KEYS do
  local n = redis.call('INCR', KEYS[i])
  if n == 1 then
    redis.call('EXPIRE', KEYS[i], tonumber(ARGV[1]))
  end
  if n > tonumber(ARGV[i + 1]) then ok = 0 end
end
return ok
"""


class RedisApiKeyAttemptGuard:
    """Host-owned, source- and tenant-scoped distributed limiter."""

    def __init__(
        self,
        *,
        redis: Redis,
        identifier_key: bytes,
        window_seconds: int = 60,
        scope_limit: int = 500,
        peer_limit: int = 10,
        selector_limit: int = 30,
    ) -> None:
        if type(identifier_key) is not bytes or len(identifier_key) != 32:
            raise ValueError("32-byte keyed-bucket material required")
        if any(
            type(value) is not int or value <= 0
            for value in (window_seconds, scope_limit, peer_limit, selector_limit)
        ):
            raise ValueError("bounded positive rate policy required")
        self._redis = redis
        self._identifier_key = identifier_key
        self._window = window_seconds
        self._limits = (scope_limit, peer_limit, selector_limit)

    def _bucket(self, kind: str, *items: str) -> str:
        parts = [kind, *items]
        message = b"".join(
            len(part.encode("utf-8")).to_bytes(4, "big") + part.encode("utf-8") for part in parts
        )
        return (
            "m4q:"
            + kind
            + ":"
            + hmac.new(self._identifier_key, message, hashlib.sha256).hexdigest()
        )

    async def admit(
        self,
        *,
        scope_ref: TrustedScopeRef,
        correlation_id: CorrelationId,
        key_id: str | None,
    ) -> bool:
        peer = HOST_PEER.get()
        if not isinstance(peer, str) or not peer or not isinstance(scope_ref, TrustedScopeRef):
            return False
        keys = (
            self._bucket("scope", scope_ref.value),
            self._bucket("peer", scope_ref.value, peer),
            self._bucket("key", scope_ref.value, key_id if key_id is not None else "unknown"),
        )
        # Redis failures propagate to ApiKeyAuthenticator as technical errors.
        result = await self._redis.eval(_LUA, len(keys), *keys, self._window, *self._limits)
        return result == 1
