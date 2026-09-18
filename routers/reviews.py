"""CRUD router for Review resource with score aggregations."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from database import db
from schemas.review import Review, ReviewCreate, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=Review, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate) -> Review:
    # 404 if equipment not found
    if payload.equipment_id not in db.equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Matériel avec l'identifiant {payload.equipment_id} introuvable",
        )
    # 404 if author user not found
    if payload.author_id not in db.users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec l'identifiant {payload.author_id} introuvable",
        )

    eq = db.equipment[payload.equipment_id]
    # Business rule: owner cannot review their own equipment
    if eq.owner_id == payload.author_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le propriétaire ne peut pas évaluer son propre matériel",
        )

    new_id = db.next_review_id()
    review = Review(id=new_id, **payload.model_dump())
    db.reviews[new_id] = review
    return review


@router.get("", response_model=List[Review])
def list_reviews(
    equipment_id: Optional[int] = Query(default=None, description="Filtrer les avis par équipement"),
    min_rating: Optional[int] = Query(default=None, ge=1, le=5, description="Note minimale"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> List[Review]:
    results = list(db.reviews.values())
    if equipment_id is not None:
        results = [r for r in results if r.equipment_id == equipment_id]
    if min_rating is not None:
        results = [r for r in results if r.rating >= min_rating]
    return results[offset : offset + limit]


@router.get("/{review_id}", response_model=Review)
def get_review(review_id: int) -> Review:
    if review_id not in db.reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avis avec l'identifiant {review_id} introuvable",
        )
    return db.reviews[review_id]


@router.patch("/{review_id}", response_model=Review)
def update_review(review_id: int, payload: ReviewUpdate) -> Review:
    if review_id not in db.reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avis avec l'identifiant {review_id} introuvable",
        )
    existing = db.reviews[review_id]
    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=updates)
    db.reviews[review_id] = updated
    return updated


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int) -> None:
    if review_id not in db.reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Avis avec l'identifiant {review_id} introuvable",
        )
    del db.reviews[review_id]
