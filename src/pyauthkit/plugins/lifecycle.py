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
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from contextlib import asynccontextmanager
from typing import cast

from pyauthkit.ports.authenticator import Authenticator

from .admission import PluginGrant, _instantiate_approved, _preflight_candidates
from .discovery import PluginAdmissionRejected, PluginCandidate


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
) -> AsyncIterator[tuple[Authenticator, ...]]:
    """Load approved plugins and attempt reverse-order cleanup on every exit.

    Preflight validates all grants BEFORE importing plugin modules. Each
    successfully returned factory instance is tracked even if SPI validation
    subsequently rejects it. Partial activation and cancellation trigger
    cleanup; any remaining uncertainty is rejected, never authenticated.

    No new verifier may be loaded while the host is processing requests.
    The host is responsible for draining requests before leaving the scope.
    """
    if (
        isinstance(cleanup_timeout_seconds, bool)
        or not isinstance(cleanup_timeout_seconds, (int, float))
        or not math.isfinite(cleanup_timeout_seconds)
        or not 0 < cleanup_timeout_seconds <= 30
    ):
        raise PluginAdmissionRejected("invalid plugin cleanup timeout")

    selected = _preflight_candidates(candidates, grants=grants)
    created: list[object] = []
    try:
        for candidate, grant in selected:
            try:
                instance = _instantiate_approved(candidate, grant, on_created=created.append)
                _check_cleanup_contract(instance)
            except Exception:
                # Factories may raise exceptions containing host credentials.
                raise PluginAdmissionRejected("plugin activation rejected") from None

        yield tuple(cast(Authenticator, instance) for instance in created)
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
