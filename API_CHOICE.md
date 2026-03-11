# API Choice

- Étudiant : Alexis Carlos TERRAO BECA
- API choisie : Jikan API (Hunter x Hunter 2011)
- URL base : https://api.jikan.moe/v4
- Documentation officielle / README : https://docs.api.jikan.moe/
- Auth : None 
- Endpoints testés :
  - GET /anime/11061 (Récupération des détails de la série Hunter x Hunter 2011)
  - GET /anime/11061/characters (Récupération de la liste des personnages)
- Hypothèses de contrat (champs attendus, types, codes) :
Code HTTP : 200 attendu pour les requêtes valides, 404 pour les ID inconnus.

Structure : Réponse encapsulée dans une clé racine nommée "data".

Types : Le champ data.episodes doit être un entier (int) égal à 148.

Valeurs : Le champ data.title doit être strictement égal à "Hunter x Hunter (2011)".

- Limites / rate limiting connu :
Limite de 60 requêtes par minute.

Pas de limite quotidienne stricte, mais sensible au spam.

- Risques (instabilité, downtime, CORS, etc.) :
Code 429 (Too Many Requests) : Risque le plus élevé si les tests s'exécutent trop vite (nécessite une gestion de "retry").

Instabilité : L'API dépend de la disponibilité de MyAnimeList ; des codes 503 (Service Unavailable) peuvent survenir lors de maintenances.

Latence : Les réponses peuvent être lentes (> 500ms) selon la charge du serveur.
