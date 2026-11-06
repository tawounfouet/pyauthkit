# M7 Design Learning Card - Plugin Lifecycle

**Problem:** an approved plugin can allocate resources before a later factory fails.

**Trust boundary:** plugin discovery is inert metadata, admission comes from the host, plugin code executes in-process, and only the existing engine and policy decide final AuthN.

**Design:** managed async lifetime with metadata-first preflight, tracking before post-factory SPI validation, reverse-order best-effort `aclose`, cooperative timeout and sanitized errors.

**Concepts:** Resource Acquisition Is Initialization (scoped async), Composition Root, Strategy, exception safety, Separation of Concerns, resource ownership, cancellation semantics.

**Trade-off:** imports, factories, blocking close, noncooperative coroutines and process failure cannot be rolled back by this scope. The host must stop ingress and drain in-flight verifications before exit.

**Evidence:** partial factory failure, wrong-method plugin, reverse closing, cancelled worker, failing closer, timeout and per-host-tenant checks. No security conformity follows merely from structural tests.
