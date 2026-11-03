"""Repeatable M3-T26/T38 runner benchmark, NOT a production security SLO.

Only synthetic credentials. Results describe one CI host at one instant.
No web stack, reverse proxy, distributed store or real AttemptGuard included.
"""

import asyncio
import json
import os
import platform
import random
import resource
import statistics
import sys
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from argon2 import PasswordHasher
from argon2.low_level import Type

from pyauthkit.adapters.password.argon2id import Argon2idPasswordHashVerifier, Argon2idPolicy
from pyauthkit.adapters.password.authenticator import PasswordAuthenticator
from pyauthkit.adapters.password.memory import InMemoryPasswordCredentialResolver
from pyauthkit.application.engine import AuthenticationEngine
from pyauthkit.application.host_context import HostBinding, HostTrustCatalog
from pyauthkit.application.policy import AuthenticationPolicyGate
from pyauthkit.composition.registry import AuthenticatorRegistry
from pyauthkit.domain.evidence import EvidenceMethod, PresentedEvidence
from pyauthkit.domain.identity import ClaimedIdentity, ScopedSubjectRef
from pyauthkit.domain.request import AuthenticationRequest
from pyauthkit.domain.scope import TrustedScopeRef
from pyauthkit.domain.temporal import CorrelationId
from pyauthkit.domain.trust import TrustProfileRef
from pyauthkit.password.capacity import KDFWorkerPool
from pyauthkit.password.records import PasswordRecordStatus, PasswordVerifierRecord


class BenchmarkOnlyAllow:
    async def admit(
        self, *, scope_ref: TrustedScopeRef, correlation_id: CorrelationId,
        identifier_kind: str | None, identifier_value: str | None,
    ) -> bool:
        return True


def percentile(samples: list[float], percentage: float) -> float:
    points = sorted(samples)
    index = (len(points) - 1) * percentage / 100.0
    low = int(index)
    high = min(low + 1, len(points) - 1)
    return round(points[low] + (points[high] - points[low]) * (index - low), 3)


async def run_benchmark(*, samples_per_case: int = 18) -> dict[str, object]:
    """Observe valid, incorrect, missing at the library boundary."""
    if not 8 <= samples_per_case <= 120:
        raise ValueError("sample count outside bounded benchmark range")
    scope = TrustedScopeRef("benchmark-scope")
    policy = Argon2idPolicy()
    hasher = PasswordHasher(
        memory_cost=19456, time_cost=2, parallelism=1, hash_len=32, type=Type.ID
    )
    record = PasswordVerifierRecord(
        scope_ref=scope,
        subject_ref=ScopedSubjectRef("benchmark-subject", "benchmark-issuer", scope),
        encoded_hash=hasher.hash(b"synthetic-correct-phrase"),
        status=PasswordRecordStatus.ACTIVE,
        version=1,
    )
    resolver = InMemoryPasswordCredentialResolver(
        {(scope.value, "username", "present"): (record,)}
    )
    workers = KDFWorkerPool(max_workers=1, max_inflight=2, memory_budget_kib=65536)
    try:
        authenticator = PasswordAuthenticator(
            resolver=resolver,
            attempt_guard=BenchmarkOnlyAllow(),
            hash_verifier=Argon2idPasswordHashVerifier(policy),
            workers=workers,
            dummy_hash=hasher.hash(b"synthetic-missing-phrase"),
        )
        catalog = HostTrustCatalog(
            [
                HostBinding(
                    "r", scope, TrustProfileRef("p", "v1", scope),
                    frozenset({EvidenceMethod.PASSWORD}),
                )
            ]
        )
        engine = AuthenticationEngine(
            policy=AuthenticationPolicyGate(catalog, final_rule=lambda _s, _e: True),
            registry=AuthenticatorRegistry({EvidenceMethod.PASSWORD: authenticator}),
        )
        entry = catalog.resolve_for_host_route("r")
        cases = {
            "valid": ("present", b"synthetic-correct-phrase"),
            "incorrect": ("present", b"synthetic-incorrect"),
            "missing": ("missing", b"synthetic-incorrect"),
        }
        readings: dict[str, list[float]] = {key: [] for key in cases}
        # Two warmups per case, with randomized interleaving for less bias.
        schedule = list(cases) * 2 + list(cases) * samples_per_case
        random.Random(47).shuffle(schedule)
        seen: dict[str, int] = {key: 0 for key in cases}
        expected = {"valid": "AUTHENTICATED", "incorrect": "REJECTED", "missing": "REJECTED"}
        for case in schedule:
            login, phrase = cases[case]
            req = AuthenticationRequest(
                PresentedEvidence(EvidenceMethod.PASSWORD, phrase),
                CorrelationId("benchmark-synthetic"),
                ClaimedIdentity("username", login),
            )
            before = time.perf_counter_ns()
            outcome = await engine.authenticate(req, entry=entry)
            elapsed_ms = (time.perf_counter_ns() - before) / 1_000_000.0
            if outcome.status != expected[case]:
                raise AssertionError("benchmark verification produced unexpected status")
            seen[case] += 1
            if seen[case] > 2:
                readings[case].append(elapsed_ms)
        summary = {
            key: {
                "samples": len(values),
                "p50_ms": percentile(values, 50),
                "p95_ms": percentile(values, 95),
                "p99_ms": percentile(values, 99),
                "mean_ms": round(statistics.mean(values), 3),
            }
            for key, values in readings.items()
        }
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "kind": "M3 KDF / library-boundary benchmark",
            "date_utc": datetime.now(UTC).isoformat(),
            "sha": os.environ.get("GITHUB_SHA", "unversioned-local"),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "argon2_cffi": version("argon2-cffi"),
            "parameters": {"memory_kib": 19456, "time_cost": 2, "parallelism": 1},
            "worker_configuration": {"max_workers": 1, "max_inflight": 2},
            "peak_rss_kib_linux": rss if sys.platform.startswith("linux") else None,
            "results": summary,
            "unknown_to_incorrect_p50_ratio": round(
                summary["missing"]["p50_ms"] / summary["incorrect"]["p50_ms"], 3
            ),
            "limitations": (
                "CI-host-only, finite samples, no statistical indistinguishability "
                "claim, no distributed store or HTTP, no real rate-limit guarantee"
            ),
        }
    finally:
        await asyncio.to_thread(workers.close)


def main() -> None:
    report = asyncio.run(run_benchmark())
    print(json.dumps(report, indent=2, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        p = Path(summary)
        cases = report["results"]
        with p.open("a", encoding="utf-8") as output:
            output.write("\n### M3 Argon2id synthetic CI timings (informative only)\n")
            output.write("\n| Case | p50 ms | p95 ms | p99 ms |\n|---|---:|---:|---:|\n")
            for name, measures in cases.items():
                output.write(
                    f"| {name} | {measures['p50_ms']} | {measures['p95_ms']} "
                    f"| {measures['p99_ms']} |\n"
                )
            output.write(
                "\nNot a production SLO, constant-time guarantee, "
                "or network-level enumeration qualification.\n"
            )


if __name__ == "__main__":
    main()
