"""Cryptographic password verification port, independent of any KDF library."""

from typing import Protocol


class PasswordHashVerifier(Protocol):
    """A synchronous KDF port. The async caller must bound worker resources."""

    @property
    def max_memory_cost_kib(self) -> int: ...

    def validate_hash(self, encoded_hash: str) -> None:
        """Reject unapproved algorithm/version/cost before expensive KDF work."""
        ...

    def verify(self, *, password: bytes, encoded_hash: str) -> bool:
        """Return False only for a wrong secret; technical faults raise."""
        ...

    def needs_rehash(self, *, encoded_hash: str) -> bool:
        """Information only; M3 never writes upgraded credentials."""
        ...


class InvalidPasswordHash(Exception):
    """An invalid/unapproved stored verifier; never expose hash contents."""


class PasswordHashProcessingError(Exception):
    """Backend could not verify an otherwise approved password verifier."""
