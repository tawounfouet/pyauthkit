"""Real Argon2id vectors and malicious PHC rejection before KDF work."""

import pytest
from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.ports.password_hashing import InvalidPasswordHash


@pytest.fixture(scope="module")
def verifier() -> Argon2idPasswordHashVerifier:
    return Argon2idPasswordHashVerifier(Argon2idPolicy())


@pytest.fixture(scope="module")
def encoded() -> str:
    return PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1, type=Type.ID).hash(
        b"long-unique-passphrase-for-qualification"
    )


def test_real_argon2id_correct_and_incorrect_password(
    verifier: Argon2idPasswordHashVerifier, encoded: str
) -> None:
    assert verifier.verify(password=b"long-unique-passphrase-for-qualification", encoded_hash=encoded)
    assert not verifier.verify(password=b"not-the-right-password", encoded_hash=encoded)


def test_real_argon2id_rehash_information_only(
    verifier: Argon2idPasswordHashVerifier, encoded: str
) -> None:
    assert isinstance(verifier.needs_rehash(encoded_hash=encoded), bool)


@pytest.mark.parametrize(
    "malicious",
    [
        "$argon2i$v=19$m=19456,t=2,p=1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2d$v=19$m=19456,t=2,p=1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2id$v=16$m=19456,t=2,p=1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2id$v=19$m=9999999,t=2,p=1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2id$v=19$m=19456,t=999,p=1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2id$v=19$m=19456,t=2,p=99$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAA",
        "$argon2id$v=19$m=19456,t=2,p=1$small$small",
        "$argon2id$v=19$m=19456,t=2,p=1$AAAA#$AAAAAAAAAAAAAAAAAAAAAA",
    ],
)
def test_malicious_and_alternative_phc_rejected_before_kdf(
    verifier: Argon2idPasswordHashVerifier, malicious: str
) -> None:
    with pytest.raises(InvalidPasswordHash):
        verifier.validate_hash(malicious)


def test_disabled_kdf_downgrade_profiles_are_rejected() -> None:
    with pytest.raises(ValueError):
        Argon2idPolicy(memory_cost_kib=1024)
    with pytest.raises(ValueError):
        Argon2idPolicy(time_cost=1)
