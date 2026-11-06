"""Verify a fixed published Argon2id PHC sample, independently sourced.

Source: https://argon2-cffi.readthedocs.io/en/stable/index.html
"""

import pytest

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.ports.password_hashing import InvalidPasswordHash

PUBLISHED_ARGON2ID = (
    "$argon2id$v=19$m=65536,t=3,p=4$MIIRqgvgQbgj220jfp0MPA"
    "$YfwJSVjtjSU0zzV/P3S9nnQ/USre2wvJMjfCIjrTQbg"
)


def test_m3_t14_published_argon2id_vector_interoperates_with_adapter() -> None:
    verifier = Argon2idPasswordHashVerifier(Argon2idPolicy())
    assert verifier.verify(
        password=b"correct horse battery staple", encoded_hash=PUBLISHED_ARGON2ID
    )
    assert not verifier.verify(password=b"wrong-phrase", encoded_hash=PUBLISHED_ARGON2ID)
    assert verifier.needs_rehash(encoded_hash=PUBLISHED_ARGON2ID)


def test_m3_t10_corrupted_published_tag_never_authenticates() -> None:
    verifier = Argon2idPasswordHashVerifier(Argon2idPolicy())
    modified = PUBLISHED_ARGON2ID[:-1] + "A"
    assert not verifier.verify(password=b"correct horse battery staple", encoded_hash=modified)


@pytest.mark.parametrize(
    "invalid",
    [
        PUBLISHED_ARGON2ID.replace("$argon2id$", "$argon2i$"),
        PUBLISHED_ARGON2ID.replace("m=65536", "m=999999"),
        PUBLISHED_ARGON2ID.replace("t=3", "t=999"),
        PUBLISHED_ARGON2ID.replace("p=4", "p=999"),
        PUBLISHED_ARGON2ID + "$unexpected",
        PUBLISHED_ARGON2ID.replace("v=19", "v=16"),
    ],
)
def test_m3_t11_t12_t13_published_vector_unsafe_mutations_refused(invalid: str) -> None:
    verifier = Argon2idPasswordHashVerifier(Argon2idPolicy())
    with pytest.raises(InvalidPasswordHash):
        verifier.validate_hash(invalid)
