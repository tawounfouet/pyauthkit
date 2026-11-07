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
## SPI v2: dependances explicites approuvees par l'hote (candidat #87)

SPI v1 reste **strictement** `pyauthkit.authenticators.v1` avec factory sans argument et `SPI_MAJOR=1`. Pour un plugin exigeant des ports hote, declarer un **nouvel entry point** dans `pyauthkit.authenticators.v2`, avec factory `create(services: PluginHostServices)` et `SPI_MAJOR=2`. Aucune conversion automatique v1/v2 ni fallback d'activation n'est admis.

```toml
[project.entry-points."pyauthkit.authenticators.v2"]
host-scoped = "my_extension.factory:create"
```

```python
from pyauthkit.domain.evidence import EvidenceMethod
from pyauthkit.plugins import (
    ENTRY_POINT_GROUP_V2,
    PluginGrant,
    PluginHostServices,
    activate_approved_authenticators,
    discover_authenticator_plugins,
)

# host_snapshot et verifier_approuve proviennent d'une configuration operateur
# HORS donnees HTTP; verifier_approuve est un port objet, PAS une cle brute.
grant = PluginGrant(
    distribution="my-extension",
    version="1.2.3",
    group=ENTRY_POINT_GROUP_V2,
    spi_major=2,
    name="host-scoped",
    target="my_extension.factory:create",
    method=EvidenceMethod.API_KEY,
    port_roles=frozenset({"hash_verifier"}),
)
services = PluginHostServices.from_snapshot(
    host_snapshot,
    route_id="host-approved-route",
    method=EvidenceMethod.API_KEY,
    ports={"hash_verifier": verifier_approuve},
)
candidates = discover_authenticator_plugins(enabled=True, group=ENTRY_POINT_GROUP_V2)
async with activate_approved_authenticators(
    candidates,
    grants=(grant,),
    service_bindings={grant: services},
) as authenticators:
    # Composer via M6, demarrer le host et attendre le drain des requetes
    # avant de quitter ce scope. Aucun chargement de plugin a la requete.
    ...
```

Le mapping de ports est copie en dictionnaire immuable. Les roles candidats sont `record_resolver.resolve`, `attempt_guard.admit`, `hash_verifier.verify`, `key_resolver.resolve`, `clock.now`, `event_sink.emit`. Les objets doivent etre livres et scopes par l'hote. Une valeur `str`/`bytes` ne constitue pas un port de confiance. Le bundle n'exporte ni credentials bruts ni valeurs dans son `repr`.

Le wrapper ajoute avant la composition refuse toute tentative dont methode, scope, profil ou correlation ne correspond pas au binding hote. **Limite majeure :** un authenticator v2 est lie a une route/un scope; la registry M2 reste indexee par methode. Ne pas reutiliser le meme plugin v2 dans un autre tenant via une seconde route. Pour plusieurs tenants, composer des runtimes distincts ou attendre un routage explicitement revu. Une API multi-tenant generale n'est pas fournie par ce SPI.

Le groupe v2 n'est pas une sandbox ni une signature de distribution. Le port host-owned peut conserver un secret ou un handle; le code du plugin s'execute dans le processus hote et peut y acceder. Un `PluginHostServices` cree par un client ou un header HTTP n'acquiert aucune autorite. L'hote valide provenance, permissions, revocation, timeout et fermeture de ses propres ports. La factory v2 n'est activable que dans le scope **gere**; le chargeur synchrone v1 rejette v2.

Le smoke de la wheel `qualification/m7_sdk/synthetic_plugin` emploie un port HMAC avec cle fixe **publique et synthetique** uniquement pour le test du mecanisme : validite du MAC, refus de revocation, blocage tenant croise et policy finale. Ce n'est pas un verifier de credentials pour la production.
## T19 - Capabilities de ports autorisees par le host

SPI v2 exige maintenant `PluginGrant.port_roles: frozenset[str]` non vide et valide pour `EvidenceMethod`. Le contrat de capabilities est **operateur-owned**, jamais fourni par le plugin ou le request. Le preflight compare l'ensemble exact des roles du grant avec les cles du `PluginHostServices.ports`; aucun port additionnel ou manquant n'est admis avant `EntryPoint.load()`.

Rôles autorises au stade M7 : `PASSWORD` et `API_KEY` peuvent recevoir `record_resolver`, `attempt_guard`, `hash_verifier`, `clock` ou `event_sink`; `JWT` peut recevoir `record_resolver`, `attempt_guard`, `key_resolver`, `clock` ou `event_sink`. L'hote doit choisir seulement le sous-ensemble necessaire. SPI v1 n'accepte aucun `port_roles`.

Une methode Python `verify` ou `resolve` n'est **pas** une garantie de securite ni une attestation de provenance. Les ports host-owned peuvent porter des ressources sensibles, et le plugin s'execute dans le meme processus. Le controle method-role est une restriction de configuration, pas une preuve cryptographique.

Pour un exemple autonome execute depuis la wheel sans extras, voir [le contrat de capabilities](m7-capability-contract.md). Pour l'admission effective d'un plugin externe, utiliser le smoke M7 de distribution synthetique installee en CI. Tous deux restent des exemples non production.

## Prevention des collisions avant l'import (T17)

Le host doit inventorier les methodes des authenticators deja composes et les transmettre dans le parametre `reserved_methods` du loader synchrone v1 ou de `activate_approved_authenticators` pour le scope gere v1/v2. Exemple de valeur hote : `reserved_methods=(EvidenceMethod.PASSWORD,)`. Ce parametre ne provient jamais des headers, des credentials ou d'un manifeste de plugin non fiable.

Le preflight valide les methodes reservees avec tous les grants **avant** d'appeler `EntryPoint.load()`. Un conflit refuse donc l'activation sans importer le plugin. Sans inventaire de l'hote, la registry M2 refuse toujours la collision a la composition, mais le code tiers peut deja avoir ete execute. Le parametre est une obligation explicite de l'integrateur lorsqu'il combine des authenticators internes et des plugins.

## Confidentialite des exceptions de ports (T24)

`PluginHostServices` capture et expurge les erreurs ordinaires provenant des descripteurs de port et des mappings, y compris les erreurs a la lecture des objets avant chargement d'un plugin. Le scope gere expurge egalement les exceptions des mappings de grants. Les messages publics ne contiennent pas les valeurs d'exception brutes. Ces defenses ne peuvent pas empecher un plugin Python approuve de journaliser des secrets lui-meme, d'effectuer un acces reseau ou de produire des effets de bord. Les ports sensibles doivent etre audites et geres par le host.

## Périmètre de provenance : metadata != octets importés (P0, #89)

Le contrôle de distribution, de version et de cible confirme uniquement des **métadonnées installées**. Python importe la cible de l'entry point selon `sys.path` et `sys.modules`, pas selon un mécanisme garantissant qu'elle provient des fichiers de la distribution approuvée. Un module homonyme placé plus tôt dans le chemin d'import peut ainsi être exécuté même lorsque le grant est exact.

M7 recontrôle désormais les métadonnées de l'entry point et le grant **immédiatement avant** `EntryPoint.load()`. Ce contrôle refuse les modifications détectables de la cible entre le preflight global et le chargement. Il ne garantit **ni** l'origine du module importé **ni** l'absence de course après ce dernier contrôle.

Pour une exploitation réelle, l'opérateur doit qualifier séparément la chaîne de construction et de déploiement (artefact approuvé, digest hors bande, provenance et permissions du système de fichiers, environnement d'import non modifiable, dépendances vérifiées, revue du code tiers). Un artefact signé, à lui seul, ne garantit pas l'isolation d'un plugin Python in-process. Ce contrat de confiance n'est pas encore implémenté et GATE27-08 est **NO-GO**.

Preuves de développement : `tests/security/test_m7_plugin_admission.py` couvre la dérive de métadonnées avant import et démontre la limite par un module de test homonyme. Dossier : `docs/qualification/M7_PLUGIN_ORIGIN_AND_IMPORT_SHADOWING_2026-11-07.md`. ADR 0042, issue #89. **Ne pas interpréter le test de shadowing comme un test de sécurité réussi.**

## Frontieres et risques

1. Discovery est desactivee par defaut et lit uniquement les metadonnees des `EntryPoint`. Aucun `EntryPoint.load()` n'est appele dans cette phase.
2. Les grants verifient nom canonique de distribution, version installee, groupe, nom, cible, methode et majeure SPI. La correspondance doit etre exacte.
3. Tous les grants sont controles avant le premier `load()` ; les distributions inconnues sont ignorees, et toute ambiguite ou exigence non satisfaite refuse le bootstrap.
4. `EntryPoint.load()` execute du code tiers avec les privileges du processus hote. Ce composant ne verifie pas de signature cryptographique d'artefact et n'offre pas d'isolation OS.
5. Apres chargement, la version SPI, la factory, la methode `EvidenceMethod` et le comportement `async verify` sont controles. Ce sont des controles structurels, pas une qualification de l'algorithme.
6. Le host transmet `reserved_methods` pour refuser des collisions connues avant import. La registry existante refuse aussi les doublons a la composition, mais potentiellement apres execution du code de la factory si le host a omis cette liste.
7. Les exceptions traitees par les frontieres d'admission et de ports sont expurgees. Cela ne garantit pas la confidentialite des sorties/logs volontaires du plugin. Les effets d'un import ou d'une factory deja executee ne sont pas annulables.
8. Ne pas faire de hot reload, de chargement a la requete, de fallback de methode ou de selection de plugin a partir de donnees client.

Une methode au-dela des `EvidenceMethod` existantes demande une evolution distincte du domaine et un nouveau gate. Le SPI v1 ne promet pas de compatibilite globale `1.0`.

## Vérification préinstallation d'un artefact wheel (candidat #89)

Avant toute installation d'une distribution tierce, le pipeline hôte peut appeler `pyauthkit.plugins.artifacts.verify_preinstall_wheel_digest(wheel_path, expected_sha256=approved_digest, grant=operator_grant)`; `approved_digest` doit provenir d'un **registre ou canal indépendant approuvé par l'opérateur**, pas de la wheel téléchargée elle-même. Ce helper refuse les SHA divergents, les identités name/version différentes et les cibles d'entry point non approuvées, sans extraire ni importer le plugin. Une wheel validée **n'autorise pas automatiquement l'activation**; la découverte/grant et les contrôles de privilèges restent distincts. Le digest ne prouve pas l'origine du module que `EntryPoint.load()` pourrait réellement exécuter après installation. ADR 0043 et issue #89.
