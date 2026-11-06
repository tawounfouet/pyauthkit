# PyAuthKit M7 - Authenticator Plugin SPI v1 et admission

Statut : contrat de developpement pre-alpha. Une metadata de distribution n'est pas une signature et l'admission n'est pas une sandbox.

## Publication d'un plugin

La distribution Python du tiers declare un entry point dans son `pyproject.toml` :

```toml
[project.entry-points."pyauthkit.authenticators.v1"]
synthetic = "my_extension.authenticator:create"
```

Le symbole `create` est un callable sans argument. Il expose `SPI_MAJOR = 1` et renvoie un objet conforme au port deja existant `pyauthkit.ports.authenticator.Authenticator` :

```python
# Exemple uniquement synthetique : ne prouve aucune authentification.
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.domain.outcome import RejectedOutcome


class AlwaysReject:
    @property
    def method(self) -> EvidenceMethod:
        return EvidenceMethod.API_KEY

    async def verify(self, request, context) -> RejectedOutcome:
        return RejectedOutcome()


def create() -> AlwaysReject:
    return AlwaysReject()


create.SPI_MAJOR = 1
```

Un plugin ne produit ni `Authenticated` ni des permissions PyIAMKit. Il ne choisit ni scope ni trust profile, ne modifie pas la policy finale et ne s'enregistre pas tout seul.

## Admission par le host

```python
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.plugins import (
    PluginGrant,
    discover_authenticator_plugins,
    load_approved_authenticators,
)

# Configuration host-owned, pas des headers ou des claims JWT.
grants = (
    PluginGrant(
        distribution="my-extension",
        version="1.2.3",
        name="synthetic",
        target="my_extension.authenticator:create",
        method=EvidenceMethod.API_KEY,
    ),
)

# 1. Aucun code de plugin charge lors de la decouverte.
candidates = discover_authenticator_plugins(enabled=True)

# 2. Preflight sur toutes les admissions puis chargement explicite.
authenticators = load_approved_authenticators(candidates, grants=grants)

# 3. Composer avec les authenticators admis via le composition root M6.
# runtime = compose_authentication_engine(snapshot, authenticators=authenticators)
```

Le code ci-dessus suppose une distribution approuvee et une version exacte reellement installee. L'exemple `AlwaysReject` reste intentionnellement non positif. La composition M6 generique refuse les chemins de secrets et JWT qui exigent des compositions specialisees : **ne pas contourner ces preflights** pour brancher un plugin.

## Cycle de vie des plugins avec ressources

Le loader synchrone `load_approved_authenticators` est une interface non proprietaire des ressources. Il convient exclusivement aux plugins volontairement stateless ou a ceux dont le host assume integralement le cleanup. Pour un plugin possedant des ressources, preferer `activate_approved_authenticators` qui expose un scope asynchrone gere.

```python
from pyauthkit.plugins import activate_approved_authenticators


async def run_host(candidates, grants, snapshot, serve):
    async with activate_approved_authenticators(candidates, grants=grants) as authenticators:
        runtime = compose_authentication_engine(snapshot, authenticators=authenticators)
        await serve(runtime)  # Stop ingress and drain before leaving the scope.
```

Une instance peut exposer `async def aclose(self) -> None`. Les closers sont appeles en ordre inverse, avec un timeout de 3 secondes par instance par defaut et un maximum configurable de 30 secondes. Une methode `close()` synchrone sans `aclose()` n'est pas prise en charge par le scope gere.

Une erreur durant l'import ou la factory peut deja avoir produit des effets collateraux. Un closer non cooperatif, une deuxieme annulation forcee ou un crash peut empecher la fermeture. Le host est responsable d'arreter l'ingress et de laisser finir les requetes en cours avant de liberer les instances. Ni le cleanup ni le SPI ne fournissent une sandbox, une annulation atomique ou une isolation de processus.
## Contrat de preuve positive pour plugin admis (candidat SPI v1)

Un authenticator approuve qui a **reellement verifie sa preuve et sa validite temporelle** peut appeler `pyauthkit.plugins.verification.issue_verified_outcome` avec `request`, `context` host, `subject`, `principal_type` et `verified_at`. Cette fonction ne verifie **aucun** mot de passe, signature, MAC, nonce ni revocation. Elle ne renvoie que le `VerifiedOutcome` **interne** du moteur, jamais un `Authenticated` final.

La declaration refuse toute incoherence entre la methode de l'evidence et celle du contexte, les correlation IDs, le scope du sujet et le scope/profil de confiance. Le moteur controle ensuite la liaison au **meme** `attempt_token` et la policy finale de l'hote. Un test prouve qu'un resultat `VerifiedOutcome` valide reste `REJECTED` lorsque la policy finale refuse.

```python
from pyauthkit.plugins.verification import issue_verified_outcome

# Uniquement APRES verification cryptographique, revocation et fraicheur.
outcome = issue_verified_outcome(
    request=request,
    context=context,
    subject=verified_scoped_subject,
    principal_type=verified_principal_type,
    verified_at=verified_timestamp,
)
```

Les identifiants `verified_scoped_subject`, `verified_principal_type` et `verified_timestamp` sont des resultats de verification de l'authenticator, pas des claims client convertis en identite. Le code ci-dessus est un extrait de SPI, pas un tutorial autonome ni une recette cryptographique.

Le plugin d'exemple `qualification/m7_sdk/synthetic_plugin` contient un cas positif **synthetique, volontairement forgeable** a partir de bytes publics. Il sert uniquement a verifier la separation outcome/policy et la distribution wheel, **jamais** a authentifier un utilisateur reel. Toute confiance production exige un verifier cryptographique qualifie, ses dependances hote et la revue de l'admission.

Voir `docs/adr/0038-m7-positive-proof-declaration-spi.md` et le blocage d'injection des dependances d'un plugin a factory zero-argument. Aucun droit d'autorisation ou de session n'est produit ici.
## Frontieres et risques

1. Discovery est desactivee par defaut et lit uniquement les metadonnees des `EntryPoint`. Aucun `EntryPoint.load()` n'est appele dans cette phase.
2. Les grants verifient nom canonique de distribution, version installee, groupe, nom, cible, methode et majeure SPI. La correspondance doit etre exacte.
3. Tous les grants sont controles avant le premier `load()` ; les distributions inconnues sont ignorees, et toute ambiguite ou exigence non satisfaite refuse le bootstrap.
4. `EntryPoint.load()` execute du code tiers avec les privileges du processus hote. Ce composant ne verifie pas de signature cryptographique d'artefact et n'offre pas d'isolation OS.
5. Apres chargement, la version SPI, la factory, la methode `EvidenceMethod` et le comportement `async verify` sont controles. Ce sont des controles structurels, pas une qualification de l'algorithme.
6. La registry existante est construite et gelee avant trafic. Les collisions de methode avec des authenticators internes sont refusees au bootstrap.
7. Toute exception est expurgee. Une factory ayant deja execute du code peut avoir eu des effets de bord : le host reste responsable de la revue du plugin, des ressources et du shutdown.
8. Ne pas faire de hot reload, de chargement a la requete, de fallback de methode ou de selection de plugin a partir de donnees client.

Une methode au-dela des `EvidenceMethod` existantes demande une evolution distincte du domaine et un nouveau gate. Le SPI v1 ne promet pas de compatibilite globale `1.0`.
