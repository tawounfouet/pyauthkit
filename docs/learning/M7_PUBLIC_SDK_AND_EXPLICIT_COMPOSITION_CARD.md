# M7 Design Learning Card - Public SDK and explicit composition

Probleme : un integrateur veut une API simple sans deplacer l'autorite AuthN vers le client.

Trust boundary : evidence non fiable + configuration hote verifiee + gate final interne.

Invariant : un resultat `Authenticated` exige verification et decision finale, meme si l'import SDK est ergonomique.

Solution la plus simple : re-exports publics deliberees et reutilisation du vrai `compose_authentication_engine`, plutot qu'un second moteur, une nouvelle abstraction de token ou une mega facade.

Concepts : Separation of Concerns, Dependency Inversion, Facade pattern uniquement si une facade ajoute une vraie simplification, API compatibility, semantic contracts, fail-closed. Ici le choix pedagogique est de **ne pas** ajouter une nouvelle classe sans besoin.

Preuve requise : quickstart execute, snapshot public, imports isolables, tests negatifs, wheel smoke. Limite : API publique != qualification de cryptographie.
