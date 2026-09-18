# Journal de Bord - Projet API GearShare

## 1. Choix du thème et des ressources

Pour ce projet, nous avons retenu le thème d'une **plateforme de location de matériel entre particuliers et professionnels (GearShare)**. Ce domaine permet d'illustrer des cas concrets de gestion de catalogue, de calendrier et de sécurité.

Les 5 ressources retenues sont :
1. **`Category`** : Permet de classifier le matériel et d'alimenter les filtres de recherche.
2. **`User`** : Représente les acteurs de la plateforme (propriétaires bailleurs et clients locataires).
3. **`Equipment`** : Le cœur du catalogue, enrichi d'une sous-liste d'accessoires requis ou optionnels (`Accessory`).
4. **`Rental`** : La réservation temporelle d'un équipement par un utilisateur, calculant dynamiquement le tarif selon la durée.
5. **`Review`** : Les retours d'expérience et notes (1 à 5 étoiles) post-location.

---

## 2. Choix de validation notables

- **Imbrication et typage fort** : L'utilisation d'une classe dédiée `Accessory` imbriquée dans `Equipment` garantit qu'aucun matériel ne peut être créé avec des accessoires mal structurés.
- **Validations inter-champs (`model_validator`)** :
  - Sur `Equipment`, la caution (`security_deposit`) doit obligatoirement être supérieure ou égale au tarif journalier (`daily_rate`).
  - Sur `Rental`, la date de fin (`end_date`) doit être strictement postérieure ou égale à la date de début (`start_date`).
- **Validateurs unitaires de champs (`field_validator`)** :
  - Assainissement systématique des chaînes de caractères (interdiction des espaces blancs comme faux libellés).
  - Validation du format du numéro de téléphone par expression régulière (formats français standardisés).

---

## 3. Gestion de la sécurité et masquage des données

Pour satisfaire les exigences du **Palier 4**, nous avons dissocié les schémas internes/stockage des schémas de présentation sortants (`response_model`) :
- Pour les utilisateurs : `UserPublicResponse` exclut strictement `hashed_password`.
- Pour les réservations : `RentalPublicResponse` exclut `internal_notes` (notes de contentieux, vérifications internes d'identité).

---

## 4. Difficulté rencontrée et solution apportée

- **Problème** : Lors du contrôle de disponibilité pour les réservations, des réservations simultanées pouvaient se chevaucher sur le même matériel, entraînant des conflits de mise à disposition physique.
- **Solution** : Nous avons implémenté au niveau du routeur `rentals.py` un algorithme de détection de recouvrement temporel `(StartA <= EndB) and (EndA >= StartB)` filtrant les réservations actives ou confirmées. En cas de chevauchement, une exception `HTTPException(400)` explicite est retournée avec l'identifiant de la réservation en conflit et ses dates.
