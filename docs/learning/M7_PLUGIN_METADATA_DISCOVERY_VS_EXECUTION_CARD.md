# M7 Design Learning Card - Discovery, admission, execution

Probleme : un entry point peut sembler declaratif tout en faisant executer le code d'un plugin lorsque \`load()\` est invoque.

Frontiere : metadata installee non fiable -> approbation hote exacte -> import et factory -> verifier admis -> registry gelee -> politique finale.

Invariant : discovery ne doit jamais appeler load ou instancier des objets tiers ; un plugin non approuve ne peut pas atteindre l'authentification.

Design : petite pipeline explicite, descriptor immutable, grant immutable, validation de toutes les identites avant execution, puis check SPI avant composition. Patterns pertinents : Strategy pour Authenticator, Registry/Composition Root pour les instances approuvees, Fail Closed pour les erreurs. Un \`Protocol\` et une dataclass ne sont pas une sandbox.

Menaces : dependency confusion, metadata spoofing, collision d'entry points, effets de bord au chargement, exceptions contenant secrets, mutation de methode, ressources non fermees.

Preuve : fausse distribution installable avec sentinelle d'import, tests de mismatch, erreurs, timeout, duplicate et integration M6. Risque residuel majeur : execution de code dans le processus hote avec ses privileges.
