"""Pydantic models for Equipment and nested Accessory sub-objects."""
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from schemas.enums import EquipmentStatus


class Accessory(BaseModel):
    """Palier 2: Sous-objet imbriqué dans l'équipement."""
    name: str = Field(..., min_length=2, max_length=50, description="Nom de l'accessoire")
    serial_number: Optional[str] = Field(default=None, max_length=50, description="Numéro de série de l'accessoire")
    is_essential: bool = Field(default=True, description="Indique si l'accessoire est indispensable au fonctionnement")


class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, description="Désignation du matériel")
    description: Optional[str] = Field(default="", max_length=1000)
    category_id: int = Field(..., gt=0, description="ID de la catégorie associée")
    owner_id: int = Field(..., gt=0, description="ID du propriétaire (User)")
    daily_rate: float = Field(..., ge=1.0, le=5000.0, description="Tarif journalier de location en euros")
    security_deposit: float = Field(..., ge=0.0, le=20000.0, description="Montant de la caution requise")
    status: EquipmentStatus = Field(default=EquipmentStatus.AVAILABLE, description="Disponibilité du matériel")
    accessories: List[Accessory] = Field(default_factory=list, description="Liste d'accessoires fournis avec le matériel")

    @model_validator(mode="after")
    def validate_deposit_against_daily_rate(self) -> "EquipmentBase":
        """Palier 2: model_validator comparant deux champs entre eux."""
        if self.security_deposit < self.daily_rate:
            raise ValueError(
                f"La caution ({self.security_deposit}€) ne peut pas être inférieure au tarif journalier ({self.daily_rate}€)"
            )
        return self


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    category_id: Optional[int] = Field(default=None, gt=0)
    owner_id: Optional[int] = Field(default=None, gt=0)
    daily_rate: Optional[float] = Field(default=None, ge=1.0, le=5000.0)
    security_deposit: Optional[float] = Field(default=None, ge=0.0, le=20000.0)
    status: Optional[EquipmentStatus] = None
    accessories: Optional[List[Accessory]] = None


class Equipment(EquipmentBase):
    id: int
