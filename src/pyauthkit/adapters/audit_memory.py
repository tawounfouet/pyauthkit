"""Non-durable, bounded, synthetic audit sink for contract tests."""

from pyauthkit.ports.events import AuthenticationEvent


class InMemoryAuthenticationEventSink:
    """Ack of an in-process call is never a persistent audit receipt."""

    __slots__ = ("_events", "_capacity")

    def __init__(self, *, capacity: int = 1000) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 10000:
            raise ValueError("invalid audit capacity")
        self._events: list[AuthenticationEvent] = []
        self._capacity = capacity

    @property
    def events(self) -> tuple[AuthenticationEvent, ...]:
        return tuple(self._events)

    async def emit(self, event: AuthenticationEvent) -> None:
        if not isinstance(event, AuthenticationEvent):
            raise ValueError("invalid audit event")
        if len(self._events) >= self._capacity:
            raise RuntimeError("audit sink full")
        self._events.append(event)

    def __repr__(self) -> str:
        return "InMemoryAuthenticationEventSink(<non-durable>)"
