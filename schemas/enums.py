"""Common enums used across domain schemas."""
from enum import Enum


class EquipmentStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"


class RentalStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
