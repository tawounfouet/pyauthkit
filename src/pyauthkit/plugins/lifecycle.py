"""Optional managed lifetime for explicitly admitted authenticator plugins.

The host must stop accepting requests and drain in-flight verifications before
leaving this scope. aclose is a best-effort resource release, not sandboxing
or a rollback of factory/import side effects. Sync close is intentionally
unsupported in this async lifecycle.
"""

import asyncio
import inspect
import math
import sys
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Mapping
from contextlib import asynccontextmanager
from typing import cast

from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.ports.authenticator import Authenticator

from .admission import PluginGrant, _instantiate_approved, _preflight_candidates
from .discovery import PluginAdmissionRejected, PluginCandidate
from .services import PluginHostServices


def _check_cleanup_contract(instance: object) -> None:
    """Avoid silent resource leaks from unsupported synchronous closers."""
    aclose = getattr(instance, "aclose", None)
    close = getattr(instance, "close", None)
    if aclose is not None and not inspect.iscoroutinefunction(aclose):
        raise PluginAdmissionRejected("unsupported plugin cleanup contract")
    if callable(close) and aclose is None:
        raise PluginAdmissionRejected("unsupported synchronous plugin cleanup")


async def _close_instances(instances: list[object], timeout_seconds: float) -> bool:
    """Try all async closers in reverse creation order, recording any failure."""
    failure = False
    for instance in reversed(instances):
        try:
            closer = getattr(instance, "aclose", None)
            if closer is None:
                if callable(getattr(instance, "close", None)):
                    failure = True
                continue
            if not inspect.iscoroutinefunction(closer):
                failure = True
                continue
            callback = cast(Callable[[], Awaitable[object]], closer)
            await asyncio.wait_for(callback(), timeout=timeout_seconds)
        except (Exception, asyncio.CancelledError):
            failure = True
    return failure


@asynccontextmanager
async def activate_approved_authenticators(
    candidates: Iterable[PluginCandidate],
    *,
    grants: Iterable[PluginGrant],
    cleanup_timeout_seconds: float = 3.0,
    service_bindings: Mapping[PluginGrant, PluginHostServices] | None = None,
    reserved_methods: Iterable[EvidenceMethod] | None = None,
) -> AsyncIterator[tuple[Authenticator, ...]]:
    """Load approved plugins and attempt reverse-order cleanup on every exit.

    Preflight validates all grants BEFORE importing plugin modules. Each
    successfully returned factory instance is tracked even if SPI validation
    subsequently rejects it. Partial activation and cancellation trigger
    cleanup; any remaining uncertainty is rejected, never authenticated.

    A host may reserve already-composed method names to reject collisions
    before import. No verifier may be loaded while serving live requests.
    The host is responsible for draining requests before leaving the scope.
    """
    if (
        isinstance(cleanup_timeout_seconds, bool)
        or not isinstance(cleanup_timeout_seconds, (int, float))
        or not math.isfinite(cleanup_timeout_seconds)
        or not 0 < cleanup_timeout_seconds <= 30
    ):
        raise PluginAdmissionRejected("invalid plugin cleanup timeout")

    # A malformed or hostile mapping must not leak a raw value or exception.
    try:
        bindings = {} if service_bindings is None else dict(service_bindings)
    except Exception:
        raise PluginAdmissionRejected("invalid plugin host service mapping") from None
    if service_bindings is None and reserved_methods is None:
        # Preserve the original v1 bootstrap call for existing integrations.
        selected = _preflight_candidates(candidates, grants=grants)
    else:
        selected = _preflight_candidates(
            candidates,
            grants=grants,
            service_bindings=bindings,
            reserved_methods=() if reserved_methods is None else reserved_methods,
        )
    created: list[object] = []
    admitted: list[Authenticator] = []
    try:
        for candidate, grant in selected:
            try:
                instance = _instantiate_approved(
                    candidate,
                    grant,
                    on_created=created.append,
                    services=bindings.get(grant),
                )
                # The raw verifier owns aclose, not the v2 scope guard wrapper.
                _check_cleanup_contract(created[-1])
                admitted.append(instance)
            except Exception:
                # Factories may raise exceptions containing host credentials.
                raise PluginAdmissionRejected("plugin activation rejected") from None

        yield tuple(admitted)
    finally:
        # Cleanup is scheduled independently so a cancellation of the caller
        # does not cancel the close task. A second forced cancellation or
        # process termination still cannot guarantee cleanup.
        already_failing = sys.exc_info()[0] is not None
        task = asyncio.create_task(_close_instances(created, cleanup_timeout_seconds))
        try:
            failed = await asyncio.shield(task)
        except asyncio.CancelledError:
            await task
            raise
        if failed and not already_failing:
            raise PluginAdmissionRejected("plugin shutdown failed") from None
