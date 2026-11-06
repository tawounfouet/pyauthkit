# M7 Public API - Manifest 0.1.0a1

Statut : API de developpement pre-alpha. L'absence d'une API dans ce manifeste ne constitue pas une promesse de stabilite.

| Surface | Symboles et role | Garantie |
| --- | --- | --- |
| `pyauthkit.sdk` | `AuthenticationEngine`, `AuthenticationRequest`, `PresentedEvidence`, `EvidenceMethod`, `AuthenticationResult`, variants de resultat | Re-exports explicites ; pas de second moteur |
| `pyauthkit.sdk` | `HostBinding`, `HostTrustCatalog`, `TrustedEntryContext`, `TrustedScopeRef`, `TrustProfileRef` | Contexte produit par catalogue hote |
| `pyauthkit.sdk` | `ConfigurationSnapshot`, `ConfigurationGeneration`, `AuditDeliveryPolicy`, `SourceProvenance` | Objets M6 valides et immuables |
| `pyauthkit.sdk` | `compose_authentication_engine`, `M6Runtime` | Composition M6 re-utilisee et preflights conserves |
| `pyauthkit.sdk` | `AuthenticatorRegistryBuilder`, `AuthenticatorRegistry` | Registration explicite, snapshot gele |
| `pyauthkit.plugins` | `PluginCandidate`, `PluginGrant`, discovery et admission | Surface SPI pre-alpha, opt-in |
| `pyauthkit.plugins.verification` | `issue_verified_outcome`, `PluginProofDeclarationRejected` | Declaration de preuve interne par plugin approuve et correctement verifie ; ni proof verifier ni `Authenticated` final |
| `pyauthkit.ports.authenticator` | `Authenticator`, `VerificationContext` | SPI existant, compatibilite majeure 1 pour plugins M7 |
| `pyauthkit.application._verification`, `configuration.bootstrap._compose_approved_runtime` | Helpers internes | NON publics |
| `pyauthkit.configuration.receipted_audit` | Audit avec recu experimental M6 | NON integre au SDK public, NO-GO production |

Le point d'entree existant du moteur est `await engine.authenticate(request, entry=trusted_entry)`, **pas** `trusted_entry=...` comme mot-clef. Le code du client ne peut pas detenir les autorites de configuration de l'hote par le seul contenu d'un request.

## Compatibilite et dependances

- Version du paquet : `0.1.0a1`, pre-alpha sans promesse SemVer stable.
- Core sans dependance requise a Django, FastAPI, AWS, Argon2 ou PyJWT.
- Extras existants : `password`, `jwt`, `aws`, `qualification`. Les extras ne sont pas importes par `pyauthkit.sdk`.
- `src/pyauthkit/py.typed` doit etre inclus dans la wheel.
- Pas de support officiel Django/Flask dans cette milestone ; la reference HTTP M6 est une qualification separee.
