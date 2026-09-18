# Journal de Tests Manuels et Automatisés (TESTS.md)

Ce document répertorie les cas de succès et cas d'échec testés sur l'ensemble des routes de l'API.

---

## 1. Routes de Catégories (`/categories`)

- **`GET /categories`**
  - *Succès* : `GET /categories` -> `200 OK`, liste contenant au moins les 3 catégories initiales.
- **`POST /categories`**
  - *Succès* : `POST /categories` avec `{"name": "Jardinage", "description": "Outils de jardin"}` -> `201 Created`, ID auto-incrémenté attribué.
  - *Échec* : `POST /categories` avec `{"name": "   "}` -> `422 Unprocessable Entity`, validation anti-chaîne vide déclenchée.
  - *Échec* : `POST /categories` avec `{"name": "Audiovisuel"}` -> `400 Bad Request`, nom de catégorie déjà existant.
- **`GET /categories/{id}`**
  - *Succès* : `GET /categories/1` -> `200 OK`, détails de la catégorie retournés.
  - *Échec* : `GET /categories/999` -> `404 Not Found`, message d'erreur clair.
- **`PATCH /categories/{id}`**
  - *Succès* : `PATCH /categories/1` avec `{"description": "Nouvelle description"}` -> `200 OK`.
  - *Échec* : `PATCH /categories/999` avec `{"name": "Inconnu"}` -> `404 Not Found`.
- **`DELETE /categories/{id}`**
  - *Succès* : `DELETE /categories/{id_cree_sans_equipement}` -> `204 No Content`.
  - *Échec* : `DELETE /categories/1` (catégorie ayant des équipements rattachés) -> `400 Bad Request`, refus d'intégrité relationnelle.

---

## 2. Routes Utilisateurs (`/users`)

- **`POST /users`**
  - *Succès* : `POST /users` avec payload complet -> `201 Created`, réponse conforme à `UserPublicResponse` sans `hashed_password`.
  - *Échec* : `POST /users` avec numéro de téléphone `phone = "0123"` -> `422 Unprocessable Entity`, rejeté par le regex.
  - *Échec* : `POST /users` avec un email déjà existant -> `400 Bad Request`.
- **`GET /users/{id}`**
  - *Succès* : `GET /users/1` -> `200 OK`, `hashed_password` exclu.
  - *Échec* : `GET /users/9999` -> `404 Not Found`.
- **`DELETE /users/{id}`**
  - *Échec* : `DELETE /users/1` (propriétaire d'équipements existants) -> `400 Bad Request`, suppression bloquée.

---

## 3. Routes Équipements (`/equipment`)

- **`POST /equipment`**
  - *Succès* : `POST /equipment` avec tarif valide et liste d'accessoires -> `201 Created`.
  - *Échec (Field ge)* : `POST /equipment` avec `daily_rate = 0.5` -> `422 Unprocessable Entity` (`daily_rate` doit être >= 1.0).
  - *Échec (model_validator)* : `POST /equipment` avec `security_deposit = 10` et `daily_rate = 50` -> `422 Unprocessable Entity` (caution inférieure au tarif).
  - *Échec (intégrité)* : `POST /equipment` avec `category_id = 9999` -> `404 Not Found`.
- **`GET /equipment` (Recherche, Filtrage, Pagination, Tri)**
  - *Succès (filtrage)* : `GET /equipment?category_id=1` -> `200 OK`, seuls les équipements audiovisuels sont renvoyés.
  - *Succès (recherche)* : `GET /equipment?search=Sony` -> `200 OK`, filtre insensible à la casse.
  - *Succès (pagination)* : `GET /equipment?limit=1&offset=1` -> `200 OK`, un seul résultat renvoyé.
  - *Succès (tri)* : `GET /equipment?sort_by=-daily_rate` -> `200 OK`, ordre décroissant de prix.
  - *Échec (tri invalide)* : `GET /equipment?sort_by=champ_inconnu` -> `400 Bad Request`.
- **`POST /equipment/{id}/duplicate` (Bonus)**
  - *Succès* : `POST /equipment/1/duplicate` -> `201 Created`, duplication profonde avec copie des accessoires et nom suffixé par `(Copie)`.
- **`GET /equipment/export/csv` (Bonus)**
  - *Succès* : `GET /equipment/export/csv` -> `200 OK`, fichier CSV avec en-têtes retourné.

---

## 4. Routes Réservations (`/rentals`)

- **`POST /rentals`**
  - *Succès* : `POST /rentals` avec dates futures valides -> `201 Created`, calcul dynamique automatique du montant total.
  - *Échec (model_validator dates)* : `POST /rentals` avec `end_date` antérieure à `start_date` -> `422 Unprocessable Entity`.
  - *Échec (règle métier propriétaire)* : `POST /rentals` où le `renter_id` est le propriétaire du matériel -> `400 Bad Request`.
  - *Échec (détection conflit dates)* : `POST /rentals` sur équipement déjà réservé sur la même plage -> `400 Bad Request`.
- **`GET /rentals/{id}`**
  - *Succès* : `GET /rentals/1` -> `200 OK`, champ `internal_notes` soigneusement masqué.

---

## 5. Routes Avis (`/reviews`)

- **`POST /reviews`**
  - *Succès* : `POST /reviews` avec note 5 et commentaire constructif -> `201 Created`.
  - *Échec (Field le=5)* : `POST /reviews` avec `rating = 6` -> `422 Unprocessable Entity`.
  - *Échec (règle métier auto-évaluation)* : Le propriétaire tente d'évaluer son propre équipement -> `400 Bad Request`.

---

## 6. Routes Analytiques & Recherche (`/stats` & `/search`)

- **`GET /stats`**
  - *Succès* : `GET /stats` -> `200 OK`, agrégation en direct des compteurs, moyennes de prix, notes moyennes et catégorie la plus populaire.
- **`GET /search` (Bonus)**
  - *Succès* : `GET /search?q=Sony` -> `200 OK`, recherche transversale sur catégories, équipements, utilisateurs et avis.
