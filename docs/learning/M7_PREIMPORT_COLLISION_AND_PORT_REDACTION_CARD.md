# M7 Learning Card - Before-import collision guards and exception redaction

**Probleme :** rejeter un doublon en phase de composition n'efface pas les effets d'un import deja execute. Un port Python peut lever un message contenant un secret pendant l'inspection.

**Contrainte de confiance :** les methodes des authenticators internes et les ports sont sous autorite hote; les metadata de distribution et les objets plugin ne le sont pas.

**Pattern :** Preflight + Composition Root + Fail Closed + Defense in Depth. Le premier controle rejette la collision avant l'import, la registry gelee M2 conserve la garantie finale.

**Implementation :** `reserved_methods` transmis par le host au chargeur v1 ou au scope v2; validation de types et confrontation a tous les grants. Validation des descripteurs/mappings dans un bloc d'exception expurge.

**Trade-off :** la library ne peut pas inventer l'inventaire hote, ni proteger contre des logs volontaires d'un plugin malveillant; l'execution in-process n'est pas une sandbox.

**Preuve :** tests adversariaux avec sentinelle d'import et canary, Ruff + mypy strict + CI multi-OS. Les resultats automatises ne remplacent pas un audit externe.
