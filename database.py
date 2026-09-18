"""In-memory data store with atomic sequence IDs and helper seeds."""
from datetime import date, datetime
from typing import Dict, List
from schemas.category import Category
from schemas.enums import EquipmentStatus, RentalStatus
from schemas.equipment import Accessory, Equipment
from schemas.rental import Rental
from schemas.review import Review
from schemas.user import User


class InMemoryDatabase:
    def __init__(self) -> None:
        self.categories: Dict[int, Category] = {}
        self.users: Dict[int, User] = {}
        self.equipment: Dict[int, Equipment] = {}
        self.rentals: Dict[int, Rental] = {}
        self.reviews: Dict[int, Review] = {}

        self._category_seq: int = 0
        self._user_seq: int = 0
        self._equipment_seq: int = 0
        self._rental_seq: int = 0
        self._review_seq: int = 0

        self.seed_defaults()

    def next_category_id(self) -> int:
        self._category_seq += 1
        return self._category_seq

    def next_user_id(self) -> int:
        self._user_seq += 1
        return self._user_seq

    def next_equipment_id(self) -> int:
        self._equipment_seq += 1
        return self._equipment_seq

    def next_rental_id(self) -> int:
        self._rental_seq += 1
        return self._rental_seq

    def next_review_id(self) -> int:
        self._review_seq += 1
        return self._review_seq

    def seed_defaults(self) -> None:
        # Categories
        cat1 = Category(id=self.next_category_id(), name="Audiovisuel", description="Caméras, micros et éclairages pro")
        cat2 = Category(id=self.next_category_id(), name="Bricolage", description="Outillage électroportatif et gros œuvre")
        cat3 = Category(id=self.next_category_id(), name="Camping", description="Tentes, réchauds et matériel de randonnée")
        self.categories = {cat1.id: cat1, cat2.id: cat2, cat3.id: cat3}

        # Users
        u1 = User(
            id=self.next_user_id(),
            full_name="Alice Martin",
            email="alice.martin@example.com",
            phone="0612345678",
            hashed_password="hashed_secret_alice_123",
            is_active=True,
        )
        u2 = User(
            id=self.next_user_id(),
            full_name="Bob Dupont",
            email="bob.dupont@example.com",
            phone="0798765432",
            hashed_password="hashed_secret_bob_456",
            is_active=True,
        )
        u3 = User(
            id=self.next_user_id(),
            full_name="Claire Fontaine",
            email="claire.fontaine@example.com",
            phone="0655443322",
            hashed_password="hashed_secret_claire_789",
            is_active=True,
        )
        self.users = {u1.id: u1, u2.id: u2, u3.id: u3}

        # Equipment
        eq1 = Equipment(
            id=self.next_equipment_id(),
            name="Sony Alpha A7 IV",
            description="Appareil photo hybride plein format 33MP avec optique 24-70mm",
            category_id=cat1.id,
            owner_id=u1.id,
            daily_rate=75.0,
            security_deposit=1200.0,
            status=EquipmentStatus.AVAILABLE,
            accessories=[
                Accessory(name="Objectif Sony 24-70mm f/2.8", serial_number="OBJ-9941", is_essential=True),
                Accessory(name="Batterie NP-FZ100", serial_number="BAT-110", is_essential=True),
                Accessory(name="Trépied carbone Manfrotto", serial_number=None, is_essential=False),
            ],
        )
        eq2 = Equipment(
            id=self.next_equipment_id(),
            name="Perforateur Bosch GBH 2-28 F",
            description="Perforateur burineur professionnel 880W SDS Plus",
            category_id=cat2.id,
            owner_id=u2.id,
            daily_rate=25.0,
            security_deposit=200.0,
            status=EquipmentStatus.RENTED,
            accessories=[
                Accessory(name="Jeu de forets béton SDS", serial_number=None, is_essential=True),
                Accessory(name="Mandrin interchangeable", serial_number="MAN-002", is_essential=False),
            ],
        )
        eq3 = Equipment(
            id=self.next_equipment_id(),
            name="Tente MSR Hubba Hubba NX 2P",
            description="Tente dôme ultralégère 3 saisons pour bivouac",
            category_id=cat3.id,
            owner_id=u1.id,
            daily_rate=18.0,
            security_deposit=150.0,
            status=EquipmentStatus.AVAILABLE,
            accessories=[
                Accessory(name="Kit piquets aluminium", is_essential=True),
                Accessory(name="Housse imperméable", is_essential=True),
            ],
        )
        self.equipment = {eq1.id: eq1, eq2.id: eq2, eq3.id: eq3}

        # Rentals
        r1 = Rental(
            id=self.next_rental_id(),
            equipment_id=eq2.id,
            renter_id=u3.id,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
            status=RentalStatus.ACTIVE,
            internal_notes="Caution réglée par chèque, identité vérifiée",
            total_cost=150.0,
        )
        self.rentals = {r1.id: r1}

        # Reviews
        rev1 = Review(
            id=self.next_review_id(),
            equipment_id=eq1.id,
            author_id=u3.id,
            rating=5,
            comment="Matériel en parfait état, capteur d'une propreté exemplaire. Propriétaire très arrangeant.",
            created_at=datetime.utcnow(),
        )
        self.reviews = {rev1.id: rev1}


# Global database instance
db = InMemoryDatabase()
