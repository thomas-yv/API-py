"""Main FastAPI entrypoint for GearShare API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    categories_router,
    equipment_router,
    rentals_router,
    reviews_router,
    stats_router,
    users_router,
)

app = FastAPI(
    title="GearShare API - Plateforme de Location de Matériel",
    description=(
        "API RESTful de gestion de location de matériel (audiovisuel, bricolage, camping, etc.). "
        "Intègre la validation stricte Pydantic V2, pagination, tri, filtrage, masquage de données sensibles, "
        "statistiques dynamiques et recherche globale unifiée."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs modulaires
app.include_router(categories_router)
app.include_router(users_router)
app.include_router(equipment_router)
app.include_router(rentals_router)
app.include_router(reviews_router)
app.include_router(stats_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "project": "GearShare API",
        "status": "operational",
        "documentation": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
