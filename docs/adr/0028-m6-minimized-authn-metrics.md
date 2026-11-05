# ADR-0028 - Metrics project only low-cardinality AuthN dimensions

Date: 2026-11-05
Status: PROPOSED / NOT APPROVED

## Problem

Copying a security event into metrics labels can disclose correlation IDs,
subjects, token claims, tenant IDs and provider URLs, and can exhaust the
metrics backend through unbounded label cardinality. Counters and spans do not
prove durable audit capture.

## Candidate decision

Define a narrow `AuthenticationMetricsSample` port with only a validated
`EvidenceMethod`, outcome from three fixed values and bounded duration in
seconds. Labels are exactly `method` and `outcome`, never copied from the
raw event or JWT. A host can explicitly compose
`BestEffortTelemetrySink(audit_sink=..., metrics_recorder=...)` and pass it to
the existing M6 event sink port, with independent bounded destination
timeouts. Missing telemetry is not automatic permission to downgrade
`required` audit (still rejected at bootstrap).

## Consequences and evidence

The in-memory recorder is bounded and test-only. There is no production
OpenTelemetry/Prometheus adapter, durability, sampling promise, exactly-once
guarantee or audit/metrics reconciliation. Counters and histograms are
recording concerns of future adapters; no trace/correlation/identity label is
admitted by the port. A hostile Python plugin already executing in the host
process is outside this in-process privacy boundary.

See `tests/security/test_m6_metrics_privacy.py`. GATE27-07 remains NO-GO.
