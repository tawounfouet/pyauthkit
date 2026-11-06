# M7 Design Learning Card - Host-Owned Plugin Dependency Injection

**Problem:** a plugin needs host-controlled resolver and verifier ports without reaching into global settings or user-controlled HTTP headers.

**Chosen approach:** new SPI major and entry-point group, immutable `PluginHostServices`, exact grants and service bindings, then managed async activation. A scoped wrapper rejects cross-tenant runtime reuse before calling the verifier.

**Patterns:** Dependency Inversion Principle, Ports and Adapters, Strategy, Composition Root, explicit versioning, Fail Closed, defensive boundaries, resource ownership.

**Why not just add `services=None` to v1?** Optional injection conceals compatibility and encourages fallback. Keeping the old signature untouched makes upgrades deliberate.

**Why a single scoped factory?** The existing M2 registry is indexed by authentication method, not tenant. One scoped authenticator cannot safely serve arbitrary tenants unless the composition is isolated or a separately reviewed scoped router is introduced.

**Test model:** host supplies a fake HMAC-verifier *object* with fixed public test key. The plugin can use that port only after admission and factory invocation. Revoke, foreign tenant, invalid token and policy denial must all fail. No real secret storage is qualified.

**Security limits:** references to mutable host ports do not make those ports immutable or trustworthy. In-process code can still access the host environment. Verified internal outcomes are not final authentication, authorization or session issuance.
