"""Pydantic models for User (Customer & Owner)."""
import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=80, description="Nom complet de l'utilisateur")
    email: EmailStr = Field(..., description="Adresse e-mail valide")
    phone: Optional[str] = Field(default=None, description="Numéro de téléphone au format français")

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        sanitized = re.sub(r"[\s\.\-]", "", value)
        if not re.fullmatch(r"(\+33|0)[1-9][0-9]{8}", sanitized):
            raise ValueError("Le format du numéro de téléphone est invalide (ex: +33612345678 ou 0612345678)")
        return sanitized


class UserCreate(UserBase):
    hashed_password: str = Field(..., min_length=8, description="Mot de passe hashé / secret de l'utilisateur")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    email: Optional[EmailStr] = Field(default=None)
    phone: Optional[str] = Field(default=None)

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        sanitized = re.sub(r"[\s\.\-]", "", value)
        if not re.fullmatch(r"(\+33|0)[1-9][0-9]{8}", sanitized):
            raise ValueError("Le format du numéro de téléphone est invalide (ex: +33612345678 ou 0612345678)")
        return sanitized


class User(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True


class UserPublicResponse(BaseModel):
    """Palier 4: response_model cachant des données sensibles (hashed_password et email masqué/caché)."""
    id: int
    full_name: str
    phone: Optional[str] = None
    is_active: bool
