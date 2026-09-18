"""CRUD router for User resource with sensitive field masking."""
from typing import List
from fastapi import APIRouter, HTTPException, status
from database import db
from schemas.user import User, UserCreate, UserPublicResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserPublicResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> User:
    # Check email uniqueness
    for existing in db.users.values():
        if existing.email.lower() == payload.email.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'adresse e-mail '{payload.email}' est déjà enregistrée",
            )
    new_id = db.next_user_id()
    user = User(id=new_id, is_active=True, **payload.model_dump())
    db.users[new_id] = user
    return user


@router.get("", response_model=List[UserPublicResponse])
def list_users() -> List[User]:
    return list(db.users.values())


@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user(user_id: int) -> User:
    if user_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {user_id} introuvable",
        )
    return db.users[user_id]


@router.patch("/{user_id}", response_model=UserPublicResponse)
def update_user(user_id: int, payload: UserUpdate) -> User:
    if user_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {user_id} introuvable",
        )
    existing = db.users[user_id]
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"]:
        for other_id, other in db.users.items():
            if other_id != user_id and other.email.lower() == updates["email"].lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"L'adresse e-mail '{updates['email']}' est déjà attribuée",
                )
    updated = existing.model_copy(update=updates)
    db.users[user_id] = updated
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int) -> None:
    if user_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {user_id} introuvable",
        )
    # Check if user owns equipment or has rentals
    owned_equipments = [eq for eq in db.equipment.values() if eq.owner_id == user_id]
    if owned_equipments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer l'utilisateur {user_id} car il possède encore {len(owned_equipments)} équipement(s)",
        )
    active_rentals = [r for r in db.rentals.values() if r.renter_id == user_id]
    if active_rentals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de supprimer l'utilisateur {user_id} car il a {len(active_rentals)} réservation(s) associées",
        )
    del db.users[user_id]
