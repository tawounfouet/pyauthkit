"""M6 experimental single-entrypoint FastAPI HTTP host.

[ARCH: Host Adapter] [SECURITY: Host Route Binding and Fail Closed]
This module is a qualification fixture, NOT a packaged production router.

A trusted host selects exactly one ReceiptedDecisionGateway and host route
at bootstrap. The incoming URL, headers, claims and body never select
a different tenant, profile, key source, underlying M2 engine or committer.

No session, cookie, authorization token or sensitive principal is issued.
Explicitly disable Uvicorn access logs, forward-proxy trust and unreviewed
middleware when hosting this reference. TLS and external ingress policies
are out of scope. This is NOT a proof of non-bypassability in other hosts.
"""

from __future__ import annotations

import asyncio
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from pyauthkit.application.host_context import HostRouteNotConfigured
from pyauthkit.configuration.receipted_audit import ReceiptedDecisionGateway
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.result import Authenticated, Rejected
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.ports.required_audit import AuditAttemptId

HEADERS = {
    "cache-control": "no-store",
    "pragma": "no-cache",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
}
REFUSAL = {"error": "invalid_credentials"}
OUTAGE = {"error": "temporarily_unavailable"}
POSITIVE = {"status": "authenticated"}


def compose_receipted_http_app(
    *,
    gateway: ReceiptedDecisionGateway,
    host_route_id: str,
    method: EvidenceMethod,
) -> FastAPI:
    """A single POST /authenticate route bound to one host-approved entry.

    This factory will never accept raw authenticators, an M6Runtime, a user
    selected route, a tenant header, or a generic credential verifier.
    """
    if type(gateway) is not ReceiptedDecisionGateway:
        raise ValueError("unapproved HTTP receipted gateway")
    if method not in (EvidenceMethod.API_KEY, EvidenceMethod.JWT):
        raise ValueError("unsupported HTTP authentication method")
    try:
        entry = gateway.catalog.resolve_for_host_route(host_route_id)
    except (HostRouteNotConfigured, TypeError):
        raise ValueError("unapproved HTTP host route") from None
    if entry.allowed_methods != frozenset({method}):
        raise ValueError("HTTP method is not host-approved")

    app = FastAPI(
        title="M6 experimental audited HTTP reference",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
        redirect_slashes=False,
    )
    required_scheme = "ApiKey " if method is EvidenceMethod.API_KEY else "Bearer "
    max_evidence = 256 if method is EvidenceMethod.API_KEY else 8192

    def response(code: int, content: dict[str, str]) -> JSONResponse:
        return JSONResponse(status_code=code, content=content, headers=HEADERS)

    @app.post("/authenticate", include_in_schema=False)
    async def authenticate(request: Request) -> JSONResponse:
        """No dynamic tenant resolution and no direct M2 endpoint.

        Auth metadata syntax errors are sent to the real gateway with the
        invalid synthetic proof and are therefore recorded as rejections.
        Requests with bodies are rejected at the HTTP framing boundary
        without consuming the body; no full-attempt audit claim is made.
        """
        # Content-Length is controlled by HTTP framing, not an auth proof.
        lengths = request.headers.getlist("content-length")
        if (
            len(lengths) > 1
            or (lengths and lengths != ["0"])
            or request.headers.getlist("transfer-encoding")
        ):
            return response(401, REFUSAL)

        values = request.headers.getlist("authorization")
        evidence = b"invalid"
        if len(values) == 1 and values[0].startswith(required_scheme):
            raw = values[0][len(required_scheme) :]
            try:
                candidate = raw.encode("ascii")
            except UnicodeError:
                candidate = b""
            if (
                1 <= len(candidate) <= max_evidence
                and not candidate.startswith(b" ")
                and not candidate.endswith(b" ")
                and b" " not in candidate
                and b"\t" not in candidate
                and b"\r" not in candidate
                and b"\n" not in candidate
            ):
                evidence = candidate

        # Neither attempt nor correlation ID is read from user headers.
        request_data = AuthenticationRequest(
            PresentedEvidence(method, evidence),
            CorrelationId(secrets.token_hex(16)),
        )
        attempt = AuditAttemptId(secrets.token_hex(16))
        try:
            result = await gateway.authenticate(
                request_data,
                entry=entry,
                attempt_id=attempt,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # No provider/SQLite/credential exception string is reflected.
            return response(503, OUTAGE)

        if isinstance(result, Authenticated):
            return response(200, POSITIVE)
        if isinstance(result, Rejected):
            return response(401, REFUSAL)
        return response(503, OUTAGE)

    return app
