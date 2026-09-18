"""Pydantic models for Rental booking."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from schemas.enums import RentalStatus


class RentalBase(BaseModel):
    equipment_id: int = Field(..., gt=0, description="ID du matériel loué")
    renter_id: int = Field(..., gt=0, description="ID de l'utilisateur locataire")
    start_date: date = Field(..., description="Date de début de location")
    end_date: date = Field(..., description="Date de fin de location")
    status: RentalStatus = Field(default=RentalStatus.PENDING, description="Statut de la réservation")
    internal_notes: Optional[str] = Field(default=None, description="Notes confidentielles de gestion interne")

    @model_validator(mode="after")
    def validate_dates_chronology(self) -> "RentalBase":
        """Palier 2: model_validator comparant start_date et end_date."""
        if self.end_date < self.start_date:
            raise ValueError(
                f"La date de fin ({self.end_date}) ne peut pas être antérieure à la date de début ({self.start_date})"
            )
        return self


class RentalCreate(RentalBase):
    pass


class RentalUpdate(BaseModel):
    equipment_id: Optional[int] = Field(default=None, gt=0)
    renter_id: Optional[int] = Field(default=None, gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[RentalStatus] = None
    internal_notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates_chronology(self) -> "RentalUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("La date de fin ne peut pas précéder la date de début")
        return self


class Rental(RentalBase):
    id: int
    total_cost: float = Field(default=0.0, ge=0.0)


class RentalPublicResponse(BaseModel):
    """Palier 4: response_model cachant internal_notes."""
    id: int
    equipment_id: int
    renter_id: int
    start_date: date
    end_date: date
    status: RentalStatus
    total_cost: float
