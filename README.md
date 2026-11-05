# PyAuthKit

A modular, framework-agnostic authentication engine for the Python ecosystem.

> **Current main:** M2 engine and ports qualified for their limited scope. Main is
> **not a production authentication system**.
>
> **M3 candidate:** Password Authentication in [draft PR #75](https://github.com/tawounfouet/pyauthkit/pull/75).
> [GATE27-04 #74](https://github.com/tawounfouet/pyauthkit/issues/74)
> remains OPEN / NOT QUALIFIED. No release or deployment is authorized.

## Architecture and trust

PyAuthKit separates **proof of authentication** from IAM identity mapping,
authorization, sessions, tokens and delegation. A request's username and
password are untrusted. The application host establishes approved
`TrustedEntryContext`, `TrustedScopeRef` and policy before the engine may
select a verifier. Only the M2 `AuthenticationPolicyGate` issues the final
`Authenticated` result.

M3's proposed password path uses:

1. A **source-scoped** `PasswordCredentialResolver` returning explicit
   `Found | Missing | Ambiguous | Unavailable` variants.
2. A real `argon2-cffi` **Argon2id-only** verifier with strict PHC
   algorithm/version/parameter bounds.
3. A bounded per-process `KDFWorkerPool`, retaining capacity after async
   cancellation until native work actually completes.
4. A **required host-supplied** `PasswordAttemptGuard` with no permissive
   production default. Network rate limiting, distributed quotas and
   response shaping remain the host's responsibility.
5. A `PasswordAuthenticator` implementing the M2 async SPI, with state,
   expiry, scope and optional source-freshness checks before returning an
   internal positive outcome. M2 still applies its mandatory final policy.

M3 has no password registration, reset, change, local SQL store, MFA,
session/token issuance, IAM permission, automatic rehash write or HTTP login UI.
The in-memory resolver is a test/demo snapshot, not a persistent auth store.

## Development

Python >=3.12; install core development dependencies:

```sh
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src/pyauthkit
```

For the opt-in M3 cryptographic implementation and its tests:

```sh
python -m pip install -e '.[dev,password]'
python -m pytest -v
```

The core package has **no unconditional Argon2 dependency**. Building a wheel
does not qualify a verifier or a specific deployment. A host must provide an
approved, scoped credential source, a mandatory admission guard, an approved
dummy Argon2id hash, bounded workers, final policy, audit integration and
security review before any live usage.

## Source documents

- [Product and system specifications](docs/specs/README.md)
- [Software Design & Learning convention](docs/specs/PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md)
- [Roadmap M0-M9](docs/specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md)
- [PR-06 execution record](docs/roadmap/PR-06_EXECUTION.md)
- [M3 security oracles](docs/qualification/M3_PR06_SECURITY_ORACLES.md)
- [M3 GATE27-04 qualification decision](docs/qualification/GATE27-04_M3_PASSWORD_AUTHENTICATION_DECISION.md) - NO-GO pending deployment-specific limits, ADR and independent review
- [Reference host qualification](qualification/host/README.md) - FastAPI, PostgreSQL, Redis and localhost HTTP, test fixtures only
- [M3 technical ADR/security review](docs/qualification/M3_SECURITY_AND_ADR_REVIEW_2026-11-05.md) - independent approval pending
- [GATE27-04 issue](https://github.com/tawounfouet/pyauthkit/issues/74)

## Security status and limitations

M2 qualification does **not** automatically qualify M3. Even when all CI
checks pass, production suitability requires review of 40 M3 scenarios,
deployment-specific rate limiting, actual credential-store consistency,
benchmarking of Argon2 memory/latency and a signed gate. A verifier in a Python
process is not a sandbox against malicious host code. Failed attempts must
not emit raw passwords, hashes or untrusted identifiers into audit channels.

See [SECURITY.md](SECURITY.md) for private security reporting. Do not post
credentials or personal data in public issues.

## License

PyAuthKit is licensed under the [MIT License](LICENSE).
