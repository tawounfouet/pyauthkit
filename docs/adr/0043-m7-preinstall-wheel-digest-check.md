# ADR 0043 - Host-approved wheel digest before plugin installation

Date: 2026-11-07
Status: PROPOSED / SECURITY REVIEW REQUIRED
Gate: GATE27-08, issue #89, PR #84

## Problem and trust boundary

A grant of distribution metadata alone cannot identify wheel bytes. A package
installer must not treat a name, version or entry point as an artifact signature.
Conversely, even a correct wheel digest does NOT prove that the Python runtime
will later import the installed code, because of import shadowing and path
mutation. These are separate problems with separate evidence requirements.

## Candidate decision

Provide a **pre-install only** helper at
`pyauthkit.plugins.artifacts.verify_preinstall_wheel_digest`. It reads a wheel
without extracting or importing modules. The caller MUST supply an exact
lowercase SHA-256 digest from an independently trusted operator-controlled
channel, plus an already validated `PluginGrant`. The function checks:

1. SHA-256 of the wheel bytes under an explicit size bound.
2. Exactly one bounded distribution METADATA file, with grant-matching name/version.
3. The exact group/name/target of the entry point in bounded entry_points.txt.
4. Duplicate archive names and trivial traversal paths are rejected.

Every violation raises a stable sanitized `PluginAdmissionRejected`. The helper
never installs packages, calls `EntryPoint.load()` or issues authentication
outcomes. It does not provide cryptographic signature verification or establish
the trustworthiness of the expected digest.

## Execution model

The host's release pipeline obtains the expected digest from its independently
controlled lock/approval record, verifies the downloaded wheel, then installs
into a deployment environment it controls. That same host must prevent mutable
import paths, preloaded shadow modules and unauthorized installation at runtime.
Those runtime invariants are not yet qualified by M7.

A test computing the expected digest from the same wheel is a test double,
**not** a trusted production provenance guarantee.

## Residual risks

- An attacker who controls both the wheel and the expected digest defeats this check.
- The wheel can be modified after verification or installed differently.
- Imports can be shadowed via sys.path, sys.modules, custom meta path finders,
  namespace packages or malicious dependencies.
- Code executes in the host process with its privileges, without a sandbox.
- There is no independent security review, deployment attestation, signed
  artifact policy or complete runtime import-origin enforcement.

## Status

IMPLEMENTED candidate only after exact source SHA and CI checks confirm it.
GATE27-08 remains NO-GO SECURITY / NO-GO PRODUCTION. Review #89 remains OPEN.
