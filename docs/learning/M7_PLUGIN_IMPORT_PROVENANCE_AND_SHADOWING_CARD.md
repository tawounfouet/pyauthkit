# M7 Learning Card - Entry Point Metadata vs Executable Code Origin

**Design question:** How do we prove a plugin is the one the operator approved, rather than merely sharing its package metadata?

**Observation:** `importlib.metadata.EntryPoint` describes a target. Its `load()` follows Python imports. A distribution grant authorizes a declared identity, not a cryptographic digest of imported code.

**Improvement:** Recheck target/group/name/distribution/version immediately before import, catching certain TOCTOU mutations after global preflight. This is Defense in Depth, not full supply-chain assurance.

**Adversarial counterexample:** A shadow module earlier in `sys.path` can execute even when the metadata grant is correct. A test that reproduces this is evidence of a **known gap**, not evidence of protection.

**Patterns:** Fail Closed, Preflight Validation, Threat Modeling, Explicit Trust Boundary, Supply Chain Provenance, TOCTOU awareness.

**Open architecture decision:** Verify an approved artifact through the deployment pipeline, constrain import resolution and runtime privileges, then examine whether a separate process boundary is required. All require an independently reviewed contract and a suitable test environment.

**Gate:** Do not publish M7 based on metadata-only matching. Issue #89 and GATE27-08 remain open.
