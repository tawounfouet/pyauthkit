# M7 Learning Card - Wheel digest vs Python import provenance

**Problem:** a wheel name and version are descriptive metadata, not proof
that the downloaded package was approved. The executed module can still
differ from the installed distribution.

**Pattern:** Defense in Depth, Fail Closed, explicit operator trust boundary,
content-addressed artifact, independent evidence, hexagonal composition root.

**Candidate:** a bounded pre-install SHA-256 inspection with an external
host-approved digest and exact grant metadata. It reads only ZIP entries,
never imports or installs the plugin.

**Why not derive the approved digest from the downloaded wheel?** That would
make the verification self-asserted, allowing any attacker-controlled wheel.

**Why not call it import attestation?** Even an approved wheel can be
overshadowed by sys.path/sys.modules or changed after inspection. Artifact
verification and executable origin are different claims.

**Proof:** tests cover approved fixture bytes, wrong digest, repackaging,
entry point mutation, invalid archives and no plugin import. No signature,
sandbox or deployment attestation is claimed.

**Gate:** TESTED is not QUALIFIED. Review #89 and GATE27-08 remain open.
