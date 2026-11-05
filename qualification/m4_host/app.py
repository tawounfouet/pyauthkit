"""Isolated FastAPI reference host for M4; NOT for deployment.

Trust is fixed by host route, not Authorization claims, tenant headers or proxy
forwarding. No credentials, sessions, access rights or audit trails are issued.
"""

import asyncio
import time
import uuid
from collections.abc import Mapping

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from pyauthkit.adapters.api_key_authenticator import ApiKeyAuthenticator
from pyauthkit.adapters.hmac_api_key import HmacApiKeyVerifier
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.ports.api_key_crypto import ApiKeyProtectionKey

from .guard import HOST_PEER, RedisApiKeyAttemptGuard
from .storage import PostgresApiKeyCredentialResolver

HEADERS = {"cache-control": "no-store", "x-content-type-options": "nosniff"}
REFUSAL = {"error": "invalid_credentials"}
OUTAGE = {"error": "temporarily_unavailable"}


class FixtureProtectionKeySource:
    """Only the explicitly configured reference key, never client-selected."""

    def __init__(self, key: bytes) -> None:
        self._key = ApiKeyProtectionKey(key)

    async def get_key(
        self, *, scope_ref: TrustedScopeRef, protection_key_ref: str
    ) -> ApiKeyProtectionKey | None:
        if scope_ref.value not in ("tenant-alpha", "tenant-beta"):
            return None
        return self._key if protection_key_ref == "key-v1" else None


def compose_app(
    *,
    pool: asyncpg.Pool,
    redis: Redis,
    verifier_key: bytes,
    bucket_key: bytes,
    routes: Mapping[str, str],
    peer_limit: int = 10,
    scope_limit: int = 500,
    selector_limit: int = 30,
    window_seconds: int = 60,
    minimum_refusal_seconds: float = 0.04,
) -> FastAPI:
    """Wire the real host adapters into M2 using an isolated fixture policy."""
    if not 0 <= minimum_refusal_seconds <= 0.5:
        raise ValueError("bounded response floor required")
    if not routes or any(not route.isalnum() for route in routes):
        raise ValueError("explicit host route catalog required")
    scopes = {route: TrustedScopeRef(scope) for route, scope in routes.items()}
    catalog = HostTrustCatalog(
        [
            HostBinding(
                route,
                scope,
                TrustProfileRef("m4-reference-only", "v1", scope),
                frozenset({EvidenceMethod.API_KEY}),
            )
            for route, scope in scopes.items()
        ]
    )
    guard = RedisApiKeyAttemptGuard(
        redis=redis,
        identifier_key=bucket_key,
        peer_limit=peer_limit,
        scope_limit=scope_limit,
        selector_limit=selector_limit,
        window_seconds=window_seconds,
    )
    authenticator = ApiKeyAuthenticator(
        resolver=PostgresApiKeyCredentialResolver(pool),
        attempt_guard=guard,
        proof_verifier=HmacApiKeyVerifier(
            key_source=FixtureProtectionKeySource(verifier_key),
            approved_refs={scope: frozenset({"key-v1"}) for scope in scopes.values()},
        ),
    )
    engine = AuthenticationEngine(
        policy=AuthenticationPolicyGate(catalog, final_rule=lambda _subject, _entry: True),
        registry=AuthenticatorRegistry({EvidenceMethod.API_KEY: authenticator}),
        timeout_seconds=3.0,
    )
    app = FastAPI(
        title="M4 qualification ONLY",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    def response(status: int, body: dict[str, str]) -> JSONResponse:
        return JSONResponse(status_code=status, content=body, headers=HEADERS)

    def build_handler(route: str):
        async def authenticate(request: Request) -> JSONResponse:
            started = time.monotonic()
            header = request.headers.get("authorization", "")
            # Missing/malformed input follows the same guarded negative path.
            evidence = b"invalid"
            if header.startswith("ApiKey "):
                try:
                    raw = header[7:].encode("ascii")
                    if 1 <= len(raw) <= 256:
                        evidence = raw
                except UnicodeError:
                    pass
            auth_request = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.API_KEY, evidence),
                CorrelationId(uuid.uuid4().hex),
            )
            peer = request.client.host if request.client is not None else None
            token = HOST_PEER.set(peer)
            try:
                result = await engine.authenticate(
                    auth_request, entry=catalog.resolve_for_host_route(route)
                )
            finally:
                HOST_PEER.reset(token)
            if isinstance(result, Authenticated):
                return response(200, {"status": "authenticated"})
            if isinstance(result, Rejected):
                remaining = minimum_refusal_seconds - (time.monotonic() - started)
                if remaining > 0:
                    await asyncio.sleep(remaining)
                return response(401, REFUSAL)
            return response(503, OUTAGE)

        return authenticate

    for route_id in scopes:
        app.add_api_route(f"/{route_id}/authenticate", build_handler(route_id), methods=["POST"])
    return app
