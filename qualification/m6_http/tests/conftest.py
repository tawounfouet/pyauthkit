"""M6 HTTP qualification fixtures: real HMAC M4, RS256 M5, local SQLite."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import socket
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import jwt
import pytest
import uvicorn
from cryptography.hazmat.primitives.asymmetric import rsa

from pyauthkit.adapters.audit_required_sqlite import (
    SqliteRequiredAuditCommitter,
    provision_sqlite_required_audit,
)
from pyauthkit.adapters.secrets_memory import SyntheticSecretResolver
from pyauthkit.configuration import (
    ConfigurationGeneration,
    SourcePolicy,
    SourceProvenance,
    load_approved_configuration,
)
from pyauthkit.configuration.receipted_integrations import (
    compose_receipted_api_key_gateway,
    compose_receipted_jwt_gateway,
)
from pyauthkit.configuration.secrets import SecretAccessPolicy, SecretGrant
from pyauthkit.domain.api_key import (
    ApiKeyFound,
    ApiKeyMissing,
    ApiKeyRecordStatus,
    ApiKeyVerifierRecord,
)
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.identity import PrincipalType, ScopedSubjectRef
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.secret import SecretRef
from pyauthkit.domain.temporal import CorrelationId, ObservedAt
from qualification.m6_http.app import compose_receipted_http_app

SCOPE = TrustedScopeRef("tenant-a:production")
REF = SecretRef("unit-vault", SCOPE.value, "hmac", "v1", "verify")
KEY = bytes(range(32, 64))
AUDIT_KEY = bytes(range(64, 96))
SELECTOR = bytes(range(16))
RAW_SECRET = bytes(range(16, 48))
NOW = 1793880000
ISSUER = "https://issuer.example.test"
AUDIENCE = "orders-api"
KEYSET = "jwk-set-approved"


class FixedClock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(NOW, UTC)


def b64(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def api_wire(secret: bytes = RAW_SECRET) -> str:
    return (b"ak1." + b64(SELECTOR) + b"." + b64(secret)).decode("ascii")


def hmac_digest() -> bytes:
    def frame(raw: bytes) -> bytes:
        return len(raw).to_bytes(4, "big") + raw

    content = b"pyauthkit-api-key-v1\x00" + b"".join(
        frame(x) for x in (SCOPE.value.encode("ascii"), b"ak1", b64(SELECTOR), RAW_SECRET)
    )
    return hmac.new(KEY, content, hashlib.sha256).digest()


class Owner:
    def __init__(self) -> None:
        self.record = ApiKeyVerifierRecord(
            scope_ref=SCOPE,
            subject_ref=ScopedSubjectRef("service-a", "issuer-a", SCOPE),
            principal_type=PrincipalType.SERVICE,
            key_id=b64(SELECTOR).decode("ascii"),
            verifier_digest=hmac_digest(),
            verifier_algorithm="hmac-sha256",
            protection_key_ref="hmac-v1",
            status=ApiKeyRecordStatus.ACTIVE,
            version=1,
            expires_at=ObservedAt(datetime(2027, 11, 5, tzinfo=UTC)),
        )

    async def resolve(self, *, scope_ref: TrustedScopeRef, key_id: str):
        if scope_ref != SCOPE or key_id != self.record.key_id:
            return ApiKeyMissing()
        return ApiKeyFound(self.record)

    async def is_current(self, *, record: ApiKeyVerifierRecord) -> bool:
        return record is self.record


class Guard:
    async def admit(
        self, *, scope_ref: TrustedScopeRef, correlation_id: CorrelationId, key_id: str | None
    ) -> bool:
        return scope_ref == SCOPE and isinstance(correlation_id, CorrelationId)


def snapshot(raw: dict[str, object]):
    return load_approved_configuration(
        raw,
        generation=ConfigurationGeneration(1),
        policy=SourcePolicy(frozenset({("host", "mapping")})),
        provenance=SourceProvenance("host", "mapping", "rev-1"),
    )


async def api_gateway(store: SqliteRequiredAuditCommitter):
    return await compose_receipted_api_key_gateway(
        snapshot({
            "schema_version": 1,
            "routes": [{
                "route_id": "api",
                "scope": SCOPE.value,
                "profile_id": "api-auth",
                "profile_version": "v1",
                "allowed_methods": ["api_key"],
            }],
            "timeout_seconds": 3.0,
            "audit_delivery": "best_effort",
            "secrets": [{
                "provider": REF.provider,
                "namespace": REF.namespace,
                "key_id": REF.key_id,
                "version": REF.version,
                "purpose": REF.purpose,
            }],
        }),
        bindings={(SCOPE, "hmac-v1"): REF},
        access_policy=SecretAccessPolicy(
            frozenset({SecretGrant("unit-vault", SCOPE.value, "verify")})
        ),
        secret_resolver=SyntheticSecretResolver({REF: KEY}),
        credential_resolver=Owner(),
        attempt_guard=Guard(),
        committer=store,
        final_rule=lambda _subject, _entry: True,
        clock=FixedClock(),
    )


def jwt_gateway(store: SqliteRequiredAuditCommitter, public: str):
    return compose_receipted_jwt_gateway(
        snapshot({
            "schema_version": 2,
            "routes": [{
                "route_id": "jwt",
                "scope": SCOPE.value,
                "profile_id": "jwt-auth",
                "profile_version": "v1",
                "allowed_methods": ["jwt"],
            }],
            "timeout_seconds": 3.0,
            "audit_delivery": "best_effort",
            "secrets": [],
            "jwt_profiles": [{
                "scope": SCOPE.value,
                "profile_id": "jwt-auth",
                "profile_version": "v1",
                "issuer": ISSUER,
                "audience": AUDIENCE,
                "expected_typ": "at+jwt",
                "allowed_algorithms": ["RS256"],
                "principal_type": "service",
                "max_token_bytes": 8192,
                "clock_skew_seconds": 0,
                "max_age_seconds": None,
                "key_source": {"kind": "static", "keyset_ref": KEYSET},
            }],
        }),
        approved_static_keysets={KEYSET: (public,)},
        committer=store,
        final_rule=lambda _subject, _entry: True,
        clock=FixedClock(),
    )


@pytest.fixture(scope="module")
def rsa_keys() -> tuple[rsa.RSAPrivateKey, str]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()

    def encoded(n: int) -> str:
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

    public = json.dumps({
        "kty": "RSA",
        "kid": "test-approved-kid",
        "use": "sig",
        "alg": "RS256",
        "n": encoded(numbers.n),
        "e": encoded(numbers.e),
    })
    return private, public


def jwt_wire(private: rsa.RSAPrivateKey, *, audience: str = AUDIENCE) -> str:
    return jwt.encode(
        {"iss": ISSUER, "aud": audience, "sub": "workload-42", "iat": NOW - 10, "exp": NOW + 300},
        private,
        algorithm="RS256",
        headers={"typ": "at+jwt", "kid": "test-approved-kid"},
    )


def store(tmp_path: Path, *, capacity: int = 100) -> SqliteRequiredAuditCommitter:
    path = tmp_path / "receipt.sqlite"
    provision_sqlite_required_audit(path)
    return SqliteRequiredAuditCommitter(
        path=path, signing_key=AUDIT_KEY, key_id="synthetic-audit-v1", capacity=capacity
    )


def stored_rows(path: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT attempt_id, outcome FROM required_audit_attempts ORDER BY sequence"
        ).fetchall()


@asynccontextmanager
async def tcp_host(gateway, *, route: str, method: EvidenceMethod) -> AsyncIterator[str]:
    app = compose_receipted_http_app(gateway=gateway, host_route_id=route, method=method)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(64)
    sock.setblocking(False)
    config = uvicorn.Config(
        app=app,
        log_level="critical",
        access_log=False,
        lifespan="off",
        proxy_headers=False,
        server_header=False,
        date_header=False,
    )
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        for _ in range(120):
            if server.started:
                break
            if task.done():
                await task
            await asyncio.sleep(0.025)
        assert server.started, "M6 reference HTTP host did not start"
        yield f"http://127.0.0.1:{sock.getsockname()[1]}"
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, timeout=8)
        sock.close()
