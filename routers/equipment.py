"""CRUD router for Equipment resource with filtering, pagination, sorting, search and duplication."""
import csv
import io
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from database import db
from schemas.enums import EquipmentStatus
from schemas.equipment import Equipment, EquipmentCreate, EquipmentUpdate

router = APIRouter(prefix="/equipment", tags=["Equipment"])


@router.post("", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate) -> Equipment:
    # Validate relational integrity: category_id
    if payload.category_id not in db.categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La catégorie avec l'identifiant {payload.category_id} n'existe pas",
        )
    # Validate relational integrity: owner_id
    if payload.owner_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'utilisateur propriétaire avec l'identifiant {payload.owner_id} n'existe pas",
        )

    new_id = db.next_equipment_id()
    item = Equipment(id=new_id, **payload.model_dump())
    db.equipment[new_id] = item
    return item


@router.get("", response_model=List[Equipment])
def list_equipment(
    category_id: Optional[int] = Query(default=None, description="Filtrer par catégorie"),
    status_filter: Optional[EquipmentStatus] = Query(default=None, alias="status", description="Filtrer par statut"),
    min_rate: Optional[float] = Query(default=None, ge=0, description="Tarif journalier minimum"),
    max_rate: Optional[float] = Query(default=None, ge=0, description="Tarif journalier maximum"),
    search: Optional[str] = Query(default=None, description="Recherche textuelle dans le nom ou la description"),
    sort_by: Optional[str] = Query(
        default=None,
        description="Champ de tri (daily_rate, name, security_deposit, id). Préfixer par '-' pour l'ordre descendant",
    ),
    offset: int = Query(default=0, ge=0, description="Index de départ pour la pagination"),
    limit: int = Query(default=10, ge=1, le=100, description="Nombre maximum d'éléments retournés"),
) -> List[Equipment]:
    """Palier 3: Filtrage, recherche query params, pagination et tri."""
    results = list(db.equipment.values())

    if category_id is not None:
        results = [eq for eq in results if eq.category_id == category_id]

    if status_filter is not None:
        results = [eq for eq in results if eq.status == status_filter]

    if min_rate is not None:
        results = [eq for eq in results if eq.daily_rate >= min_rate]

    if max_rate is not None:
        results = [eq for eq in results if eq.daily_rate <= max_rate]

    if search:
        query_str = search.lower().strip()
        results = [
            eq
            for eq in results
            if query_str in eq.name.lower() or (eq.description and query_str in eq.description.lower())
        ]

    if sort_by:
        descending = sort_by.startswith("-")
        field = sort_by.lstrip("-")
        valid_sort_fields = {"daily_rate", "name", "security_deposit", "id"}
        if field not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Champ de tri invalide '{field}'. Champs autorisés: {', '.join(valid_sort_fields)}",
            )
        results.sort(key=lambda x: getattr(x, field), reverse=descending)

    return results[offset : offset + limit]


@router.get("/export/csv")
def export_equipment_csv() -> Response:
    """Palier 5 Défi bonus: Route d'export CSV pur Python sans dépendance externe."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["id", "name", "category_id", "owner_id", "daily_rate", "security_deposit", "status", "accessories_count"])
    for eq in db.equipment.values():
        writer.writerow([
            eq.id,
            eq.name,
            eq.category_id,
            eq.owner_id,
            eq.daily_rate,
            eq.security_deposit,
            eq.status.value,
            len(eq.accessories),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=equipment_catalog.csv"},
    )


@router.get("/{equipment_id}", response_model=Equipment)
def get_equipment(equipment_id: int) -> Equipment:
    if equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {equipment_id} introuvable",
        )
    return db.equipment[equipment_id]


@router.post("/{equipment_id}/duplicate", response_model=Equipment, status_code=status.HTTP_201_CREATED)
def duplicate_equipment(equipment_id: int) -> Equipment:
    """Palier 5 Défi bonus: Duplication en profondeur d'une ressource avec ses sous-objets."""
    if equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {equipment_id} introuvable",
        )
    source = db.equipment[equipment_id]
    copied_data = source.model_dump(exclude={"id"})
    copied_data["name"] = f"{source.name} (Copie)"
    copied_data["status"] = EquipmentStatus.AVAILABLE
    new_id = db.next_equipment_id()
    duplicated = Equipment(id=new_id, **copied_data)
    db.equipment[new_id] = duplicated
    return duplicated


@router.patch("/{equipment_id}", response_model=Equipment)
def update_equipment(equipment_id: int, payload: EquipmentUpdate) -> Equipment:
    if equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {equipment_id} introuvable",
        )
    existing = db.equipment[equipment_id]
    updates = payload.model_dump(exclude_unset=True)

    if "category_id" in updates and updates["category_id"] not in db.categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La catégorie avec l'identifiant {updates['category_id']} n'existe pas",
        )
    if "owner_id" in updates and updates["owner_id"] not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"L'utilisateur propriétaire avec l'identifiant {updates['owner_id']} n'existe pas",
        )

    # Cross-field check if rate or deposit changed
    new_rate = updates.get("daily_rate", existing.daily_rate)
    new_deposit = updates.get("security_deposit", existing.security_deposit)
    if new_deposit < new_rate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La caution ({new_deposit}€) ne peut pas être inférieure au tarif journalier ({new_rate}€)",
        )

    updated = existing.model_copy(update=updates)
    db.equipment[equipment_id] = updated
    return updated


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int) -> None:
    if equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {equipment_id} introuvable",
        )
    # Check active rentals
    active_rentals = [
        r for r in db.rentals.values()
        if r.equipment_id == equipment_id and r.status in [RentalStatus.CONFIRMED, RentalStatus.ACTIVE]
    ]
    if active_rentals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer le matériel {equipment_id} car {len(active_rentals)} réservation(s) sont en cours ou confirmées",
        )
    # Delete associated reviews
    review_ids_to_del = [rid for rid, rev in db.reviews.items() if rev.equipment_id == equipment_id]
    for rid in review_ids_to_del:
        del db.reviews[rid]

    del db.equipment[equipment_id]
