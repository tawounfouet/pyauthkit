# PyAuthKit M7 - Python pur : quickstart

Statut : exemple de developpement pre-alpha, pas une recette de deploiement en production.

## Execution

Depuis le checkout PyAuthKit, dans un environnement ou le paquet est installe :

```bash
python examples/m7_pure_python.py
```

Resultat attendu : `M7 Python-only synthetic denial: REJECTED (no principal)`.

Le script assemble un `ConfigurationSnapshot`, un `HostBinding`, un `M6Runtime` et un `AuthenticationEngine` existants. L'entree hote est resolue depuis `runtime.catalog.resolve_for_host_route("host-api-route")` avant l'appel :

```python
result = await runtime.engine.authenticate(request, entry=entry)
```

**Attention** : le verifier de demonstration retourne uniquement `RejectedOutcome`. Ce n'est pas une implementation de mot de passe, d'API Key ou de JWT, et il ne doit jamais etre presente comme une preuve cryptographique. Les authenticators qualifies pour leur perimetre doivent etre composes par les chemins M3/M4/M5/M6 appropries.

## Contrat de confiance

- `AuthenticationRequest` et `PresentedEvidence` sont des donnees non fiables.
- L'application hote seule etablit le `HostTrustCatalog`, les routes approuvees et les methodes permises.
- Le client HTTP/CLI ne fournit jamais `TrustedEntryContext`, `TrustProfile` ou l'entree `entry`.
- L'authenticator produit un `AuthenticatorOutcome` interne ; le moteur et sa policy gate sont seuls responsables du resultat public.
- `Authenticated` n'implique aucune permission, session, emission de token ou resolution d'identite PyIAMKit.
- Les exemples utilisent `audit_delivery=best_effort`. Le mode `required` demeure interdit dans cette composition publique.
- Le `minimum_generation` doit etre lie a une source hote fiable si une garantie de non-retour arriere entre redemarrages est requise.

Pour des plugins tiers, lire [le guide auteur et admission](plugin-author-guide.md).
