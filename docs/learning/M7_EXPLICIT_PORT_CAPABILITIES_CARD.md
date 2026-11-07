# M7 Design Learning Card - Port Capability Grants

Status: PROPOSED / PRE-ALPHA / NOT SECURITY QUALIFIED

**Problem:** A host may accidentally inject a broader map of resolver, verifier or key-source ports than a single admitted plugin needs.

**Trust boundary:** `AuthenticationRequest` is untrusted; the host chooses the route, approved method, grant and port roles. The installed plugin's metadata is untrusted until admitted. Its Python code executes in the host process after admission.

**Solution:** An immutable operator-owned `PluginGrant.port_roles` explicitly lists the permitted role names. `PluginHostServices` validates method compatibility; the loader enforces exact equality before importing the third-party module. No fallback or dynamic role request.

**Concepts:** Least Privilege, Fail Closed, Defense in Depth, Dependency Inversion, Ports and Adapters, immutable configuration, Contract Tests, Composition Root.

**Why not inspect the verifier's capabilities at runtime?** That would require importing/executing the plugin before the operator's decision and invites policy discovery from untrusted code.

**Trade-off:** A role is a Python-level structural contract, not a secure sandbox. The contents and permissions of a port reference are not proven by its name. The plugin can still access other objects in-process.

**Executable proof:** Keep a self-contained `python` fence in `docs/guides/m7-capability-contract.md` and run it through the separate-wheel smoke. Contrast documentation tested in CI with prose and snippets still only illustrative.

**Decision:** TESTED CANDIDATE when CI succeeds. T19/T25 PARTIAL for independent security qualification and comprehensive documentation coverage.
