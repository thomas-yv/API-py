"""CRUD router for Rental bookings with status transitions, period clash verification and cost computation."""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from database import db
from schemas.enums import EquipmentStatus, RentalStatus
from schemas.rental import Rental, RentalCreate, RentalPublicResponse, RentalUpdate

router = APIRouter(prefix="/rentals", tags=["Rentals"])


def _calculate_total_cost(daily_rate: float, start_date: date, end_date: date) -> float:
    # At least 1 day
    days = max(1, (end_date - start_date).days + 1)
    return round(days * daily_rate, 2)


@router.post("", response_model=RentalPublicResponse, status_code=status.HTTP_201_CREATED)
def create_rental(payload: RentalCreate) -> Rental:
    # 404 if equipment not found
    if payload.equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {payload.equipment_id} introuvable",
        )
    # 404 if renter user not found
    if payload.renter_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locataire avec l'identifiant {payload.renter_id} introuvable",
        )

    eq = db.equipment[payload.equipment_id]

    # Business rule: owner cannot rent their own equipment
    if eq.owner_id == payload.renter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le propriétaire ne peut pas réserver son propre matériel",
        )

    # Business rule: equipment must not be retired or in maintenance
    if eq.status in [EquipmentStatus.MAINTENANCE, EquipmentStatus.RETIRED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le matériel {eq.name} n'est pas louable car son statut actuel est '{eq.status.value}'",
        )

    # Palier 5 Défi bonus: Vérification de conflit de dates sur le même équipement
    for existing_rental in db.rentals.values():
        if (
            existing_rental.equipment_id == payload.equipment_id
            and existing_rental.status in [RentalStatus.CONFIRMED, RentalStatus.ACTIVE]
        ):
            # Check date overlap: (StartA <= EndB) and (EndA >= StartB)
            if payload.start_date <= existing_rental.end_date and payload.end_date >= existing_rental.start_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Le matériel est déjà réservé sur la période demandée (Réservation #{existing_rental.id} du {existing_rental.start_date} au {existing_rental.end_date})",
                )

    total_cost = _calculate_total_cost(eq.daily_rate, payload.start_date, payload.end_date)
    new_id = db.next_rental_id()
    rental = Rental(
        id=new_id,
        total_cost=total_cost,
        **payload.model_dump(),
    )
    db.rentals[new_id] = rental
    return rental


@router.get("", response_model=List[RentalPublicResponse])
def list_rentals(
    renter_id: Optional[int] = Query(default=None, description="Filtrer par locataire"),
    equipment_id: Optional[int] = Query(default=None, description="Filtrer par équipement"),
    rental_status: Optional[RentalStatus] = Query(default=None, alias="status", description="Filtrer par statut"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Rental]:
    results = list(db.rentals.values())
    if renter_id is not None:
        results = [r for r in results if r.renter_id == renter_id]
    if equipment_id is not None:
        results = [r for r in results if r.equipment_id == equipment_id]
    if rental_status is not None:
        results = [r for r in results if r.status == rental_status]
    return results[offset : offset + limit]


@router.get("/{rental_id}", response_model=RentalPublicResponse)
def get_rental(rental_id: int) -> Rental:
    if rental_id not in db.rentals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Réservation avec l'identifiant {rental_id} introuvable",
        )
    return db.rentals[rental_id]


@router.patch("/{rental_id}", response_model=RentalPublicResponse)
def update_rental(rental_id: int, payload: RentalUpdate) -> Rental:
    if rental_id not in db.rentals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Réservation avec l'identifiant {rental_id} introuvable",
        )
    existing = db.rentals[rental_id]
    updates = payload.model_dump(exclude_unset=True)

    target_eq_id = updates.get("equipment_id", existing.equipment_id)
    if target_eq_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {target_eq_id} introuvable",
        )

    target_renter_id = updates.get("renter_id", existing.renter_id)
    if target_renter_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Locataire avec l'identifiant {target_renter_id} introuvable",
        )

    new_start = updates.get("start_date", existing.start_date)
    new_end = updates.get("end_date", existing.end_date)
    if new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de fin ne peut pas précéder la date de début",
        )

    # Recalculate cost if equipment or dates change
    eq = db.equipment[target_eq_id]
    new_cost = _calculate_total_cost(eq.daily_rate, new_start, new_end)
    updates["total_cost"] = new_cost

    updated = existing.model_copy(update=updates)
    db.rentals[rental_id] = updated
    return updated


@router.delete("/{rental_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rental(rental_id: int) -> None:
    if rental_id not in db.rentals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Réservation avec l'identifiant {rental_id} introuvable",
        )
    existing = db.rentals[rental_id]
    if existing.status == RentalStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer une location en cours d'activité (statut {existing.status.value})",
        )
    del db.rentals[rental_id]
