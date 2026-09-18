"""Routers package initialization."""
from routers.categories import router as categories_router
from routers.equipment import router as equipment_router
from routers.rentals import router as rentals_router
from routers.reviews import router as reviews_router
from routers.stats import router as stats_router
from routers.users import router as users_router

__all__ = [
    "categories_router",
    "users_router",
    "equipment_router",
    "rentals_router",
    "reviews_router",
    "stats_router",
]
