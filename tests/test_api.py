"""Comprehensive test suite for GearShare API validating all milestones (Paliers 1 to 5)."""
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from main import app
from database import db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Reset the in-memory database to seed state before each test."""
    db._category_seq = 0
    db._user_seq = 0
    db._equipment_seq = 0
    db._rental_seq = 0
    db._review_seq = 0
    db.seed_defaults()


def test_root_health():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "operational"


# ==========================================
# Palier 1: CRUD sur les 5 ressources & relations
# ==========================================

def test_categories_crud():
    # List
    res = client.get("/categories")
    assert res.status_code == 200
    assert len(res.json()) >= 3

    # Create
    res = client.post("/categories", json={"name": "Jardinage", "description": "Tondeuses et taille-haies"})
    assert res.status_code == 201
    cat_id = res.json()["id"]

    # Detail
    res = client.get(f"/categories/{cat_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Jardinage"

    # Patch
    res = client.patch(f"/categories/{cat_id}", json={"name": "Espaces Verts"})
    assert res.status_code == 200
    assert res.json()["name"] == "Espaces Verts"

    # Delete
    res = client.delete(f"/categories/{cat_id}")
    assert res.status_code == 204

    # 404 on deleted
    res = client.get(f"/categories/{cat_id}")
    assert res.status_code == 404


def test_users_crud_and_masking():
    # Create
    user_payload = {
        "full_name": "Jean Dupont",
        "email": "jean.dupont@test.com",
        "phone": "0601020304",
        "hashed_password": "super_secret_password_123",
    }
    res = client.post("/users", json=user_payload)
    assert res.status_code == 201
    created = res.json()
    assert created["full_name"] == "Jean Dupont"
    # Palier 4: hashed_password is NOT returned
    assert "hashed_password" not in created

    uid = created["id"]
    res = client.get(f"/users/{uid}")
    assert res.status_code == 200
    assert "hashed_password" not in res.json()

    # Update
    res = client.patch(f"/users/{uid}", json={"full_name": "Jean-Marc Dupont"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "Jean-Marc Dupont"

    # Delete
    res = client.delete(f"/users/{uid}")
    assert res.status_code == 204


def test_equipment_crud():
    payload = {
        "name": "Micro Cravate Rode Wireless GO II",
        "description": "Système de microphone sans fil compact double canal",
        "category_id": 1,
        "owner_id": 1,
        "daily_rate": 20.0,
        "security_deposit": 150.0,
        "status": "AVAILABLE",
        "accessories": [{"name": "Câble SC5", "is_essential": True}],
    }
    res = client.post("/equipment", json=payload)
    assert res.status_code == 201
    eq_id = res.json()["id"]

    res = client.get(f"/equipment/{eq_id}")
    assert res.status_code == 200
    assert res.json()["accessories"][0]["name"] == "Câble SC5"

    res = client.patch(f"/equipment/{eq_id}", json={"daily_rate": 22.0})
    assert res.status_code == 200
    assert res.json()["daily_rate"] == 22.0

    res = client.delete(f"/equipment/{eq_id}")
    assert res.status_code == 204


def test_rentals_crud_and_masking():
    start = date.today() + timedelta(days=1)
    end = date.today() + timedelta(days=3)
    payload = {
        "equipment_id": 1,
        "renter_id": 2,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "status": "PENDING",
        "internal_notes": "Caution en attente de vérification",
    }
    res = client.post("/rentals", json=payload)
    assert res.status_code == 201
    data = res.json()
    # Palier 4: internal_notes must NOT be exposed
    assert "internal_notes" not in data
    assert data["total_cost"] == 75.0 * 3  # 3 days * 75€

    rental_id = data["id"]
    res = client.get(f"/rentals/{rental_id}")
    assert res.status_code == 200
    assert "internal_notes" not in res.json()

    res = client.patch(f"/rentals/{rental_id}", json={"status": "CANCELLED"})
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"

    res = client.delete(f"/rentals/{rental_id}")
    assert res.status_code == 204


def test_reviews_crud():
    payload = {
        "equipment_id": 3,
        "author_id": 2,
        "rating": 4,
        "comment": "Tente très légère et rapide à monter sous la pluie !",
    }
    res = client.post("/reviews", json=payload)
    assert res.status_code == 201
    rev_id = res.json()["id"]

    res = client.get(f"/reviews/{rev_id}")
    assert res.status_code == 200
    assert res.json()["rating"] == 4

    res = client.patch(f"/reviews/{rev_id}", json={"rating": 5})
    assert res.status_code == 200
    assert res.json()["rating"] == 5

    res = client.delete(f"/reviews/{rev_id}")
    assert res.status_code == 204


# ==========================================
# Palier 2: Validations approfondies
# ==========================================

def test_pydantic_field_constraints():
    # Equipment daily_rate out of range (ge=1.0)
    res = client.post("/equipment", json={
        "name": "Objectif 50mm",
        "category_id": 1,
        "owner_id": 1,
        "daily_rate": 0.5,  # Too low
        "security_deposit": 50.0,
    })
    assert res.status_code == 422

    # Review rating out of range [1, 5]
    res = client.post("/reviews", json={
        "equipment_id": 1,
        "author_id": 2,
        "rating": 6,
        "comment": "Superbe matériel",
    })
    assert res.status_code == 422


def test_pydantic_field_validators():
    # Category name with only whitespaces
    res = client.post("/categories", json={"name": "   "})
    assert res.status_code == 422

    # Invalid phone format on User
    res = client.post("/users", json={
        "full_name": "Test Invalide",
        "email": "test@domain.com",
        "phone": "invalid_phone_123",
        "hashed_password": "password_long_123",
    })
    assert res.status_code == 422


def test_pydantic_model_validators():
    # Equipment: deposit < daily_rate
    res = client.post("/equipment", json={
        "name": "Groupe Électrogène",
        "category_id": 2,
        "owner_id": 1,
        "daily_rate": 100.0,
        "security_deposit": 50.0,  # lower than daily_rate!
    })
    assert res.status_code == 422

    # Rental: end_date < start_date
    res = client.post("/rentals", json={
        "equipment_id": 1,
        "renter_id": 2,
        "start_date": "2026-10-10",
        "end_date": "2026-10-05",  # earlier!
    })
    assert res.status_code == 422


# ==========================================
# Palier 3: Query params, filtrage, pagination, tri, stats
# ==========================================

def test_filtering_and_pagination_and_sorting():
    # Filter by category
    res = client.get("/equipment?category_id=1")
    assert res.status_code == 200
    for item in res.json():
        assert item["category_id"] == 1

    # Filter by search
    res = client.get("/equipment?search=Sony")
    assert res.status_code == 200
    assert len(res.json()) >= 1
    assert "Sony" in res.json()[0]["name"]

    # Pagination
    res = client.get("/equipment?limit=1&offset=1")
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Sorting
    res = client.get("/equipment?sort_by=-daily_rate")
    assert res.status_code == 200
    items = res.json()
    assert items[0]["daily_rate"] >= items[1]["daily_rate"]


def test_statistics_endpoint():
    res = client.get("/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_equipment"] == 3
    assert data["total_users"] == 3
    assert data["average_daily_rate_eur"] > 0
    assert "Audiovisuel" in data["most_popular_category"] or "Bricolage" in data["most_popular_category"] or "Camping" in data["most_popular_category"]


# ==========================================
# Palier 4: Robustesse & Business Exceptions
# ==========================================

def test_relational_integrity_and_business_http_exceptions():
    # 404 on unexistent category
    res = client.post("/equipment", json={
        "name": "Lampe Torche LED",
        "category_id": 9999,
        "owner_id": 1,
        "daily_rate": 10.0,
        "security_deposit": 50.0,
    })
    assert res.status_code == 404

    # 400 when owner rents their own equipment
    eq1_owner_id = db.equipment[1].owner_id
    res = client.post("/rentals", json={
        "equipment_id": 1,
        "renter_id": eq1_owner_id,
        "start_date": "2026-11-01",
        "end_date": "2026-11-03",
    })
    assert res.status_code == 400
    assert "propriétaire ne peut pas réserver" in res.json()["detail"]

    # 400 when owner reviews their own equipment
    res = client.post("/reviews", json={
        "equipment_id": 1,
        "author_id": eq1_owner_id,
        "rating": 5,
        "comment": "Auto évaluation non autorisée",
    })
    assert res.status_code == 400
    assert "propriétaire ne peut pas évaluer" in res.json()["detail"]


# ==========================================
# Palier 5: Défis bonus (Duplication, Export CSV, Recherche globale, Périodes)
# ==========================================

def test_bonus_duplicate_equipment():
    res = client.post("/equipment/1/duplicate")
    assert res.status_code == 201
    dup = res.json()
    assert dup["id"] != 1
    assert "Copie" in dup["name"]
    assert len(dup["accessories"]) == len(db.equipment[1].accessories)


def test_bonus_csv_export():
    res = client.get("/equipment/export/csv")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "Sony Alpha A7 IV" in res.text


def test_bonus_global_search():
    res = client.get("/search?q=Sony")
    assert res.status_code == 200
    data = res.json()
    assert len(data["equipment"]) >= 1
    assert data["equipment"][0]["name"] == "Sony Alpha A7 IV"


def test_bonus_rental_dates_overlap():
    # Rental 1 is booked on equipment 2 from 2026-09-10 to 2026-09-15
    res = client.post("/rentals", json={
        "equipment_id": 2,
        "renter_id": 1,
        "start_date": "2026-09-12",
        "end_date": "2026-09-14",
    })
    assert res.status_code == 400
    assert "déjà réservé sur la période demandée" in res.json()["detail"]
