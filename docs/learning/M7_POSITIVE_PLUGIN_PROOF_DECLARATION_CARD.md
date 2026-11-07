# M7 Design Learning Card - Admitted Plugin Positive Proof

> Status: PROPOSED / CODE CANDIDATE / NOT SECURITY QUALIFIED

**Problem:** How can a third-party verifier signal a successful credential check without gaining the ability to mint a final authenticated principal?

**Trust:** Untrusted evidence and tenant hints are not configuration. The host selects an admitted authenticator and gives it a per-attempt `VerificationContext`. The plugin must validate the proof. Its declaration remains provisional until the engine's attempt check and final host policy.

**Minimal contract:** One SPI helper `issue_verified_outcome` wraps the existing restricted internal constructor. It checks consistency of evidence method, trace, subject scope and profile, but intentionally does not verify cryptography. No new `AuthenticationResult` constructor is added.

**Patterns/principles:** Strategy (`Authenticator`), Dependency Inversion (host-supplied ports), Façade as a small explicit SPI helper, Fail Closed, Separation of Concerns. No capability-token theater: a Python object is not an unforgeable cryptographic attestation.

**Test evidence:** valid synthetic fixture; invalid proof; cross-tenant/client hint; mismatched trace/method/scope; stale attempt token; policy final deny. Wheel test is isolated and uses intentionally public, forgeable bytes. Its success is a qualification test, not credential security assurance.

**Limit:** In-process plugin code can import private modules or synthesize values. Host admission means trusting the code that was installed, not proving its intent. A production factory needs approved resolver/secret ports and independent review. Never ship the synthetic positive plugin in a product or describe it as real AuthN.
