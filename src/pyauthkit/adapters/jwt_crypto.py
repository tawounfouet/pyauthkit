"""RS256 JWS verification via the optional, maintained PyJWT crypto backend.

[ARCH: Adapter] The domain does not implement RSA/JWS itself. PyJWT checks
the signature against ONE host-approved algorithm and a public RSA key.
Claim semantics are subsequently enforced by JWTAuthenticator.
"""

from __future__ import annotations

from typing import cast

from pyauthkit.domain.failure import DomainTechnicalError, TechnicalErrorCode
from pyauthkit.domain.jwt import strict_json_object


class PyJwtRs256Verifier:
    """Proof adapter. Requires pyauthkit[jwt]; does not issue AuthenticationResult."""

    __slots__ = ()

    async def verify_signature(
        self, *, compact_jws: bytes, approved_key: str, approved_algorithm: str
    ) -> dict[str, object] | None:
        if approved_algorithm != "RS256":
            return None
        try:
            import jwt
        except ImportError:
            raise DomainTechnicalError(TechnicalErrorCode.INVALID_TRUST_CONFIGURATION) from None

        try:
            public_jwk = strict_json_object(approved_key.encode("utf-8"), maximum=4096)
            if (
                public_jwk.get("kty") != "RSA"
                or public_jwk.get("alg", "RS256") != approved_algorithm
                or not public_jwk.keys() <= {"kty", "kid", "alg", "use", "key_ops", "n", "e"}
            ):
                return None
            key = jwt.algorithms.RSAAlgorithm.from_jwk(approved_key)
            # An approved JWK is never allowed to carry private key material.
            if not hasattr(key, "key_size") or key.key_size < 2048:
                return None
            decoded = jwt.decode(
                compact_jws.decode("ascii"),
                key=key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                    "verify_iss": False,
                    "verify_aud": False,
                    "require": [],
                },
            )
            if not isinstance(decoded, dict):
                return None
            return cast(dict[str, object], decoded)
        except (jwt.exceptions.PyJWTError, ValueError, TypeError, UnicodeError):
            return None
