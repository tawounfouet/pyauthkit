# ADR 0036 - M7 explicit plugin admission and Authenticator SPI

Status: PROPOSED / PR-10 REVIEW
Date: 2026-11-06

## Contexte
Les entry points installes sont du metadata non fiable. Appeler \`EntryPoint.load()\` durant la decouverte execute potentiellement du code tiers avant toute approbation. L'authenticator M2 existe deja et sa registry peut etre gelee.

## Decision proposee
- Groupe \`pyauthkit.authenticators.v1\`.
- Decouverte desactivee par defaut; metadata uniquement, taille et formats bornes.
- Grant hote exact sur nom canonique de distribution, version, groupe, entry point, cible et methode.
- Preflight de tous les grants avant toute execution; refuser absence, collision et mismatch.
- Factory sans arguments avec \`SPI_MAJOR=1\`, qui retourne le port existant \`Authenticator\`.
- Controle post-load de la methode et de \`async verify\`; pas de final result expose au plugin.
- Composer exclusivement via le composition root et la policy M2/M6 existants.
- Aucune notion de signature de supply chain ou de sandbox dans cette ADR.

## Alternatives ecartees
Auto-load de tous les plugins du virtualenv, chargement a la demande de l'HTTP client, classpath scans, nouvelle couche de policy dans le plugin, ajout d'une methode runtime inconnue. Ces solutions agrandissent la frontiere de confiance ou dupliquent des decisions d'authentification.

## Risques et evolution
La metadata d'installation ne prouve pas l'integrite de l'artefact. L'admission ne confine pas un code malveillant. Une failure de factory peut laisser des effets de bord. Cycle de vie de ressources partagees, cancellation, provenance du binaire et versionnement mineur SPI restent des points de revue. Une verification independante est requise pour GATE27-08.

## Tests
Discovery sentinel, grants mismatch, collision, SPI mismatch, exception sanitized, verifier malforme, freeze et packaging wheel.
