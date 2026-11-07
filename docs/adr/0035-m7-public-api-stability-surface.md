# ADR 0035 - M7 public SDK surface

Status: PROPOSED / PR-10 REVIEW
Date: 2026-11-06

## Context
Le code M2/M6 dispose deja d'un moteur et d'une composition de confiance, mais il n'existe pas encore de catalogue d'imports publics pour les consommateurs de PyAuthKit. Un facade nouveau pourrait involontairement creer un deuxieme chemin de succes AuthN ou contourner les preflights.

## Decision proposee
Exposer un sous-package `pyauthkit.sdk` avec `__all__` explicite, re-exportant uniquement les composants M2/M6 et valeurs de domaine deja implementes. Garder le package root minimal. Conserver exactement `engine.authenticate(request, entry=...)` et la composition M6. Pas de facade sync universelle ni d'import Web/cloud par defaut.

## Consequences
Ergonomie plus previsible et manifest API testable, mais version de paquet 0.1.0a1 sans garantie SemVer 1.0. Les references aux modules internes ne deviennent pas des API publiques. Les compositions JWT/secrets specialisees conservent leur autorite.

## Verification
Test d'exports et import sans extras, quickstart installe, revue de compatibility par SHA.
