"""Argon2id adapter backed by argon2-cffi, with pre-KDF PHC cost bounds.

SECURITY: PasswordHasher.verify accepts multiple PHC variants. This adapter
explicitly permits only Argon2id v=19 and constrained cost parameters.
"""

import re
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from argon2.low_level import Type

from pyauthkit.ports.password_hashing import InvalidPasswordHash, PasswordHashProcessingError

# Reject arbitrary additional parameters, reordered formats, oversized salts and
# alternative Argon2i/d algorithms. Argon2 PHC uses unpadded base64.
_PHC = re.compile(
    r"\$argon2id\$v=19\$m=([0-9]{1,7}),t=([0-9]{1,3}),p=([0-9]{1,3})"
    r"\$([A-Za-z0-9+/]{22,86})\$([A-Za-z0-9+/]{22,86})\Z"
)


@dataclass(frozen=True, slots=True)
class Argon2idPolicy:
    """Deployment-reviewed bounds, with OWASP's minimum as a default baseline.

    Do not extrapolate a global security certification from these parameters.
    """

    memory_cost_kib: int = 19456
    time_cost: int = 2
    parallelism: int = 1
    max_memory_cost_kib: int = 65536
    max_time_cost: int = 4
    max_parallelism: int = 4

    def __post_init__(self) -> None:
        fields = (
            self.memory_cost_kib,
            self.time_cost,
            self.parallelism,
            self.max_memory_cost_kib,
            self.max_time_cost,
            self.max_parallelism,
        )
        if any(type(field) is not int for field in fields):
            raise ValueError("invalid Argon2id parameters")
        if (
            self.memory_cost_kib < 19456
            or not 2 <= self.time_cost <= self.max_time_cost <= 8
            or not 1 <= self.parallelism <= self.max_parallelism <= 8
            or not self.memory_cost_kib <= self.max_memory_cost_kib <= 262144
            or self.memory_cost_kib < 8 * self.parallelism
        ):
            raise ValueError("unapproved Argon2id configuration")


class Argon2idPasswordHashVerifier:
    """Only a verifier, not an enroller, password changer or credential store."""

    __slots__ = ("_policy", "_hasher")

    def __init__(self, policy: Argon2idPolicy) -> None:
        if not isinstance(policy, Argon2idPolicy):
            raise ValueError("Argon2id policy required")
        self._policy = policy
        self._hasher = PasswordHasher(
            time_cost=policy.time_cost,
            memory_cost=policy.memory_cost_kib,
            parallelism=policy.parallelism,
            hash_len=32,
            salt_len=16,
            type=Type.ID,
        )

    @property
    def max_memory_cost_kib(self) -> int:
        return self._policy.max_memory_cost_kib

    def validate_hash(self, encoded_hash: str) -> None:
        if not isinstance(encoded_hash, str) or len(encoded_hash) > 256:
            raise InvalidPasswordHash("unapproved password verifier")
        match = _PHC.fullmatch(encoded_hash)
        if match is None:
            raise InvalidPasswordHash("unapproved password verifier")
        memory, iterations, parallelism = (int(match.group(i)) for i in (1, 2, 3))
        if (
            not self._policy.memory_cost_kib <= memory <= self._policy.max_memory_cost_kib
            or not self._policy.time_cost <= iterations <= self._policy.max_time_cost
            or not 1 <= parallelism <= self._policy.max_parallelism
            or memory < 8 * parallelism
        ):
            raise InvalidPasswordHash("unapproved password verifier")
        # Base64 lengths are bounded in the regex; encoding must be canonical.
        # Reconstructed decoded length enforces salt/tag minima.
        import base64
        import binascii

        try:
            for value in (match.group(4), match.group(5)):
                decoded = base64.b64decode(value + "=" * (-len(value) % 4), validate=True)
                if len(decoded) < 16 or len(decoded) > 64:
                    raise InvalidPasswordHash("unapproved password verifier")
                if base64.b64encode(decoded).decode("ascii").rstrip("=") != value:
                    raise InvalidPasswordHash("unapproved password verifier")
        except (binascii.Error, ValueError) as exc:
            raise InvalidPasswordHash("unapproved password verifier") from None

    def verify(self, *, password: bytes, encoded_hash: str) -> bool:
        if type(password) is not bytes or not 1 <= len(password) <= 65536:
            raise PasswordHashProcessingError("invalid password evidence")
        self.validate_hash(encoded_hash)
        try:
            return self._hasher.verify(encoded_hash, password) is True
        except VerifyMismatchError:
            return False
        except (InvalidHashError, VerificationError, MemoryError, ValueError):
            raise PasswordHashProcessingError("password verification unavailable") from None

    def needs_rehash(self, *, encoded_hash: str) -> bool:
        self.validate_hash(encoded_hash)
        try:
            return self._hasher.check_needs_rehash(encoded_hash)
        except (InvalidHashError, VerificationError, ValueError):
            raise PasswordHashProcessingError("password verifier metadata unavailable") from None
