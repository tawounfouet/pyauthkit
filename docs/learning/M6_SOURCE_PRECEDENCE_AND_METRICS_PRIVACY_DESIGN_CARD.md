# M6 Design Learning - Source precedence and metrics privacy

Date: 2026-11-05
Status: IMPLEMENTED CANDIDATE / EVIDENCE PENDING / NOT QUALIFIED

## Problems before patterns

A system that merges multiple configurations by key can create a trust policy
nobody intended: the JWT issuer comes from one source but the approved key
source comes from another. A telemetry adapter that labels a counter with a
correlation ID can leak request metadata and create an unbounded metric series.

## Boundaries and invariants

- A host-owned authoritative configuration controls every trust-bearing field.
- An exact order of additional host-approved sources may override only
  `timeout_seconds`; no default or fallback and no cross-profile merge.
- Metrics expose only the fixed method/outcome enums and bounded duration,
  not the raw event, evidence, JWT, source, URL, user, tenant or trace.
- A metric submission is never a durable security audit receipt.

## Patterns and language

`SourceLayerPolicy` is an immutable policy Value Object. The source reader
implements explicit per-field precedence, not GoF Chain of Responsibility or
a generic ETL merge engine. `AuthenticationMetricsRecorder` is a Protocol
(DIP, Ports & Adapters) because exporter implementations genuinely vary.
`BestEffortTelemetrySink` is a fan-out adapter with independent bounded
failure semantics; it remains distinct from M2's AuthN policy.

## Rejected alternatives

Pydantic-settings implicit source order, `dict.update` of security blocks,
JWT-sourced profile discovery, unbounded metrics labels, logging an exception
message or credentials, treating audit/metrics as exactly-once, and allowing
metric export outage to switch an AuthN result.

## Tests and qualification

`test_m6_source_precedence.py` covers the exact source chain and trust
override rejection; `test_m6_metrics_privacy.py` covers bounded series,
canaries, failures and cancellation. Real exporter / multi-source trust
replacement / durable audit remain out of scope pending separate review.
