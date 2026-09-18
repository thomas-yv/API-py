"""Pydantic models for Review."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReviewBase(BaseModel):
    equipment_id: int = Field(..., gt=0, description="ID du matériel évalué")
    author_id: int = Field(..., gt=0, description="ID de l'auteur de l'avis")
    rating: int = Field(..., ge=1, le=5, description="Note attribuée entre 1 et 5")
    comment: str = Field(..., min_length=5, max_length=500, description="Commentaire d'évaluation")

    @field_validator("comment")
    @classmethod
    def validate_clean_comment(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 5:
            raise ValueError("Le commentaire doit contenir au moins 5 caractères non vides")
        return trimmed


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, min_length=5, max_length=500)

    @field_validator("comment")
    @classmethod
    def validate_clean_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            trimmed = value.strip()
            if len(trimmed) < 5:
                raise ValueError("Le commentaire doit contenir au moins 5 caractères")
            return trimmed
        return value


class Review(ReviewBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
