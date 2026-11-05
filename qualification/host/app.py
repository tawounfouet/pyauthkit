"""M3 qualification host, deliberately outside the reusable PyAuthKit package.

ASGI routes are configured by the host, not derived from a tenant field in the
JSON body. No forwarded-IP headers are trusted. Run behind a trusted proxy
only with an explicitly designed proxy trust policy.
"""

import json
from collections.abc import Mapping

import asyncpg
from argon2 import PasswordHasher
from argon2.low_level import Type
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.ports.password_hashing import PasswordHashVerifier

from .guard import HOST_SOURCE, RedisPasswordAttemptGuard
from .storage import PostgresPasswordCredentialResolver

MAX_HTTP_BYTES = 4096
BASE_HEADERS = {
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
}
REJECT_BODY = {"error": "invalid_credentials"}
ERROR_BODY = {"error": "temporarily_unavailable"}


def compose_qualification_app(
    *,
    postgres_pool: asyncpg.Pool,
    redis: Redis,
    hmac_key: bytes,
    route_scopes: Mapping[str, str],
    workers: KDFWorkerPool,
    max_per_source: int = 200,
    max_per_identity: int = 200,
    window_seconds: int = 60,
    hash_verifier: PasswordHashVerifier | None = None,
) -> FastAPI:
    """Create a reference host with explicit scope mappings.

    The large default quotas are for repeatable measurement only. Production
    security depends on operator-reviewed limits and multiple rate dimensions.
    """
    scopes = {route: TrustedScopeRef(scope) for route, scope in route_scopes.items()}
    if not scopes:
        raise ValueError("qualification host needs approved routes")

    catalog = HostTrustCatalog(
        [
            HostBinding(
                route, scope, TrustProfileRef("m3-password", "v1", scope),
                frozenset({EvidenceMethod.PASSWORD}),
            )
            for route, scope in scopes.items()
        ]
    )
    guard = RedisPasswordAttemptGuard(
        redis=redis,
        hmac_key=hmac_key,
        max_per_source=max_per_source,
        max_per_identity=max_per_identity,
        window_seconds=window_seconds,
    )
    crypto = hash_verifier if hash_verifier is not None else Argon2idPasswordHashVerifier(Argon2idPolicy())
    dummy_hash = PasswordHasher(
        memory_cost=19456,
        time_cost=2,
        parallelism=1,
        type=Type.ID,
    ).hash(b"qualification-only-dummy-material")
    authenticator = PasswordAuthenticator(
        resolver=PostgresPasswordCredentialResolver(postgres_pool),
        attempt_guard=guard,
        hash_verifier=crypto,
        workers=workers,
        dummy_hash=dummy_hash,
    )
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
        registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: authenticator}),
        timeout_seconds=2.0,
    )
    app = FastAPI(
        title="PyAuthKit M3 Qualification Host - NOT FOR PRODUCTION",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def response(status: int, payload: dict[str, str]) -> JSONResponse:
        return JSONResponse(status_code=status, content=payload, headers=BASE_HEADERS)

    def route_handler(route_id: str):
        async def login(request: Request) -> JSONResponse:
            # Bounded streaming before parsing avoids unbounded request.body().
            raw = bytearray()
            async for chunk in request.stream():
                raw.extend(chunk)
                if len(raw) > MAX_HTTP_BYTES:
                    return response(413, {"error": "invalid_request"})
            try:
                body = json.loads(raw)
                if not isinstance(body, dict) or set(body) != {"username", "password"}:
                    raise ValueError("malformed JSON login envelope")
                username = body["username"]
                password = body["password"]
                if not isinstance(username, str) or not isinstance(password, str):
                    raise ValueError("invalid login types")
                evidence = PresentedEvidence(EvidenceMethod.PASSWORD, password.encode("utf-8"))
                claim = ClaimedIdentity("username", username)
                authentication_request = AuthenticationRequest(
                    evidence=evidence,
                    correlation_id=CorrelationId("m3-qualification"),
                    claimed_identity=claim,
                )
            except (ValueError, UnicodeError, TypeError):
                return response(400, {"error": "invalid_request"})

            source = request.client.host if request.client is not None else None
            token = HOST_SOURCE.set(source)
            try:
                result = await engine.authenticate(
                    authentication_request, entry=catalog.resolve_for_host_route(route_id)
                )
            finally:
                HOST_SOURCE.reset(token)

            if isinstance(result, Authenticated):
                return response(200, {"status": "authenticated"})
            if isinstance(result, Rejected):
                return response(401, REJECT_BODY)
            return response(503, ERROR_BODY)

        return login

    for route in scopes:
        app.add_api_route(f"/{route}/login", route_handler(route), methods=["POST"])
    return app
