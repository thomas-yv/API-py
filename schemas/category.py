"""Pydantic models for Category."""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Nom de la catégorie")
    description: Optional[str] = Field(default="Aucune description fournie", max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Le nom de catégorie ne peut pas être vide ou composé uniquement d'espaces")
        return trimmed


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            trimmed = value.strip()
            if not trimmed:
                raise ValueError("Le nom de catégorie ne peut pas être vide")
            return trimmed
        return value


class Category(CategoryBase):
    id: int
