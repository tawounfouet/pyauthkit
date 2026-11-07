# ADR 0040 - Pre-import method collision guard and sanitized plugin port failures

Status: PROPOSED / SECURITY REVIEW REQUIRED
Date: 2026-11-07
Scope: M7 / PR #84, oracles M7-T17 and M7-T24

## Context

An installed plugin may be imported before the M2 registry identifies an already-owned method. An untrusted or malformed port descriptor can throw an exception containing host information during service-bundle validation.

## Decision candidate

1. Allow the host to supply exact `EvidenceMethod` values under `reserved_methods` for v1 and managed v2 activation.
2. Include reserved methods in the full admission preflight. Reject a collision before executing any approved entry-point code.
3. Preserve existing M2 duplicate-method detection at the immutable composition root as a second defensive boundary.
4. Catch and sanitize ordinary exceptions from v2 service/port descriptors and malicious mappings; do not expose underlying exception messages.
5. Keep the host responsible for accurate method inventory, vetted plugin code, port privileges and safe logging.

## Alternatives considered

- Rely only on the M2 registry: fails late, after possible third-party code execution.
- Auto-inspect arbitrary plugin objects for methods before admission: requires importing the very code being restricted.
- Treat a Python dataclass as sandbox/attestation: no isolation or origin proof is provided.
- Suppress every `BaseException`: would also mask process-level cancellation and control signals, so reject.

## Trade-offs

This is a selective trust-boundary improvement, not full third-party code isolation. A missing reserved-method inventory still permits late collision detection. `raise ... from None` sanitizes normal visible tracebacks but cannot guarantee safe behavior by malicious plugin code or ports.

## Tests

- v1 and v2 reserved method collision before import with sentinels.
- invalid reserved method sanitized, nonconflicting reserved method accepted.
- hostile v2 property descriptor, host-port mapping, service-grant mapping.
- CI source head `7a98e4545e7fccfd1c696d2555a7499b61be5394` / 13 jobs.
- Gate stays NO-GO pending independent security review.
