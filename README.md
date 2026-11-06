# PyAuthKit

Modular, framework-agnostic Python authentication library. **Pre-alpha developer integration only**.

## Current development scope

- **M0-M2**: package/bootstrap, immutable domain results, async AuthenticationEngine, host-bound trust catalog and final policy gate. Limited milestone gates GO.
- **M3 Password**: Argon2id PHC verification, scoped credential resolver, bounded KDF work and mandatory host-supplied attempt guard. Candidate development integration, **GATE27-04 NO-GO** pending independent security approval and deployment-specific qualification.
- **M4 API Key**: real scoped HMAC verification and revocation guard, merged for pre-alpha development only. **GATE27-05 security NO-GO**.
- **M5 JWT**: host-approved RS256/JOSE/JWKS verification, merged for pre-alpha development only. **GATE27-06 security NO-GO**.
- **M6 Configuration & Audit**: immutable snapshots, scoped secrets, adapters and local experimental receipted audit/HTTP reference. Merged for pre-alpha development only. **GATE27-07 NO-GO**. Public `audit_delivery=required` is deliberately rejected.
- **M7-M9**: public SDK/plugin contract, independent global qualification and release governance remain open.

**Not approved for production, use with real credentials, an auth gateway, IAM authorization or a PyPI publication.** A passing CI and merge are not independent security qualification.

## Installation and test

Requires Python 3.12 or newer in the tested combinations. Core imports without unconditional Argon2, JWT, AWS or web-framework dependencies. Optional extras may be explicitly installed:

```bash
python -m pip install -e '.[dev,password,qualification]'
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src/pyauthkit
python -m build
```

Use `pyauthkit[password]` for the optional Argon2id implementation, `pyauthkit[jwt]` for the optional JWT/cryptographic verifier and `pyauthkit[aws]` for optional boto3. The `qualification` extra is for isolated host validation, not a production deployment contract.

## Trust model

The application host selects an approved scope/profile; no credential, JWT claim, HTTP header or plugin can grant trusted tenant selection. The M2 policy gate controls issuance of `Authenticated`. Authentication is not authorization, identity provisioning, a session, an access-token issuance or a PyIAMKit permission grant.

Audit events, attempt guards, provider consistency and external network/host controls must be qualified for each admitted use case. In-process Python private attributes are not a sandbox. The experimental M6 receipt gateway is not proof of an exclusive deployment ingress or a tamper-evident distributed ledger.

## References

- [Roadmap M0-M9](docs/specs/27_PYAUTHKIT_IMPLEMENTATION_ROADMAP.md)
- [Design & Learning convention](docs/specs/PYAUTHKIT_SOFTWARE_DESIGN_LEARNING_CONVENTION.md)
- [M3 PR #75](https://github.com/tawounfouet/pyauthkit/pull/75), [GATE27-04 #74](https://github.com/tawounfouet/pyauthkit/issues/74)
- [M4 gate #77](https://github.com/tawounfouet/pyauthkit/issues/77), [M5 gate #81](https://github.com/tawounfouet/pyauthkit/issues/81), [M6 PR #82](https://github.com/tawounfouet/pyauthkit/pull/82)
- [Security policy](SECURITY.md) and [implementation documentation](docs/roadmap/README.md)

## License

MIT. See [LICENSE](LICENSE).
