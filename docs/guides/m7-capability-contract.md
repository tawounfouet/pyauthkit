# M7 - Exemple executable : roles de ports approuves

**Statut :** exemple de developpement pre-alpha, sans preuve d'authentification reelle.

Ce fichier contient un bloc Python autonome. La CI l'execute depuis une wheel PyAuthKit installee dans un environnement isole au moyen de `scripts/check_m7_doc_examples.py`. L'exemple valide la configuration des capabilities, sans charger de plugin tiers.

## Exemple Python

```python
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.plugins import (
    ENTRY_POINT_GROUP_V2,
    PluginAdmissionRejected,
    PluginGrant,
    PluginHostServices,
)
from pyauthkit.sdk import (
    AuditDeliveryPolicy,
    ConfigurationGeneration,
    ConfigurationSnapshot,
    HostBinding,
    SourceProvenance,
    TrustedScopeRef,
    TrustProfileRef,
)


class SyntheticDenyVerifier:
    def verify(self, payload: bytes, *, scope_ref: TrustedScopeRef) -> bool:
        return False


scope = TrustedScopeRef("m7-doc-tenant")
profile = TrustProfileRef("m7-doc-profile", "v1", scope)
snapshot = ConfigurationSnapshot(
    schema_version=1,
    generation=ConfigurationGeneration(1),
    provenance=SourceProvenance("m7-doc", "host", "v1"),
    bindings=(
        HostBinding("route-doc", scope, profile, frozenset({EvidenceMethod.API_KEY})),
    ),
    timeout_seconds=1.0,
    audit_delivery=AuditDeliveryPolicy(),
)
grant = PluginGrant(
    distribution="m7-doc-plugin",
    version="1.0.0",
    name="deny-only",
    target="m7_doc_plugin.factory:create",
    group=ENTRY_POINT_GROUP_V2,
    spi_major=2,
    method=EvidenceMethod.API_KEY,
    port_roles=frozenset({"hash_verifier"}),
)
services = PluginHostServices.from_snapshot(
    snapshot,
    route_id="route-doc",
    method=EvidenceMethod.API_KEY,
    ports={"hash_verifier": SyntheticDenyVerifier()},
)
assert grant.port_roles == frozenset(services.ports)
assert services.port("hash_verifier").verify(b"synthetic", scope_ref=scope) is False

try:
    PluginGrant(
        distribution="m7-doc-plugin",
        version="1.0.0",
        name="unapproved-capability",
        target="m7_doc_plugin.factory:create",
        group=ENTRY_POINT_GROUP_V2,
        spi_major=2,
        method=EvidenceMethod.API_KEY,
        port_roles=frozenset({"key_resolver"}),
    )
except PluginAdmissionRejected:
    pass
else:
    raise AssertionError("API_KEY must not approve key_resolver")

print("M7 capability guide: EXPLICIT HOST ROLES / DENY ONLY")
```

## Frontiere de confiance

- Le grant v2 et les ports sont approuves par l'hote au bootstrap, et jamais derives de l'evidence, des claims JWT ou d'un header client.
- `port_roles` doit correspondre **exactement** aux noms presents dans `PluginHostServices.ports`. Le controle d'identite du bundle et du grant est applique avant l'import du plugin.
- Pour PASSWORD et API_KEY, les roles candidats sont `record_resolver`, `attempt_guard`, `hash_verifier`, `clock` et `event_sink`.
- Pour JWT, les roles candidats sont `record_resolver`, `attempt_guard`, `key_resolver`, `clock` et `event_sink`.
- Le host ne donne que les ports effectivement necessaires. Leurs propres methodes doivent valider le scope, la fraicheur et la revocation. Une methode structurellement conforme ne prouve pas sa securite.
- Cet exemple ne charge aucun plugin; le smoke de wheel M7 valide cette etape separement avec une fixture HMAC publique, non destinee a la production.
