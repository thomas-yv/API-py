"""CRUD router for Category resource."""
from typing import List
from fastapi import APIRouter, HTTPException, status
from database import db
from schemas.category import Category, CategoryCreate, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate) -> Category:
    # Verify uniqueness of category name
    for existing in db.categories.values():
        if existing.name.lower() == payload.name.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une catégorie avec le nom '{payload.name}' existe déjà",
            )
    new_id = db.next_category_id()
    cat = Category(id=new_id, **payload.model_dump())
    db.categories[new_id] = cat
    return cat


@router.get("", response_model=List[Category])
def list_categories() -> List[Category]:
    return list(db.categories.values())


@router.get("/{category_id}", response_model=Category)
def get_category(category_id: int) -> Category:
    if category_id not in db.categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie avec l'identifiant {category_id} introuvable",
        )
    return db.categories[category_id]


@router.patch("/{category_id}", response_model=Category)
def update_category(category_id: int, payload: CategoryUpdate) -> Category:
    if category_id not in db.categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie avec l'identifiant {category_id} introuvable",
        )
    existing = db.categories[category_id]
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"]:
        for other_id, other in db.categories.items():
            if other_id != category_id and other.name.lower() == updates["name"].lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Une catégorie avec le nom '{updates['name']}' existe déjà",
                )
    updated = existing.model_copy(update=updates)
    db.categories[category_id] = updated
    return updated


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int) -> None:
    if category_id not in db.categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie avec l'identifiant {category_id} introuvable",
        )
    # Check if equipment is linked
    linked_equipments = [eq for eq in db.equipment.values() if eq.category_id == category_id]
    if linked_equipments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer la catégorie {category_id} car {len(linked_equipments)} équipement(s) y sont rattachés",
        )
    del db.categories[category_id]
