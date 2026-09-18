"""Global stats endpoint and cross-resource unified search router."""
from collections import Counter
from typing import Any, Dict, List
from fastapi import APIRouter, Query
from database import db

router = APIRouter(tags=["Analytics & Search"])


@router.get("/stats")
def get_platform_statistics() -> Dict[str, Any]:
    """Palier 3: Calcul de statistiques agrégées dynamiques en Python."""
    total_equipment = len(db.equipment)
    total_users = len(db.users)
    total_rentals = len(db.rentals)
    total_reviews = len(db.reviews)

    # Average daily rate
    avg_daily_rate = (
        round(sum(eq.daily_rate for eq in db.equipment.values()) / total_equipment, 2)
        if total_equipment > 0
        else 0.0
    )

    # Average review rating
    avg_rating = (
        round(sum(rev.rating for rev in db.reviews.values()) / total_reviews, 2)
        if total_reviews > 0
        else 0.0
    )

    # Total rental turnover revenue
    total_turnover = round(sum(r.total_cost for r in db.rentals.values()), 2)

    # Most represented category
    if db.equipment:
        cat_counts = Counter(eq.category_id for eq in db.equipment.values())
        most_common_cat_id, count = cat_counts.most_common(1)[0]
        most_common_cat_name = db.categories.get(most_common_cat_id).name if most_common_cat_id in db.categories else "Inconnue"
    else:
        most_common_cat_name = "Aucune"

    # Equipment status distribution
    status_distribution = Counter(eq.status.value for eq in db.equipment.values())

    return {
        "total_equipment": total_equipment,
        "total_users": total_users,
        "total_rentals": total_rentals,
        "total_reviews": total_reviews,
        "average_daily_rate_eur": avg_daily_rate,
        "average_review_rating": avg_rating,
        "total_revenue_eur": total_turnover,
        "most_popular_category": most_common_cat_name,
        "equipment_status_breakdown": dict(status_distribution),
    }


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=2, description="Terme recherché simultanément dans toutes les ressources"),
) -> Dict[str, Any]:
    """Palier 5 Défi bonus: Recherche globale interrogant plusieurs ressources en même temps."""
    term = q.lower().strip()

    matching_categories = [
        {"id": c.id, "name": c.name, "description": c.description}
        for c in db.categories.values()
        if term in c.name.lower() or (c.description and term in c.description.lower())
    ]

    matching_equipment = [
        {"id": eq.id, "name": eq.name, "daily_rate": eq.daily_rate, "status": eq.status.value}
        for eq in db.equipment.values()
        if term in eq.name.lower() or (eq.description and term in eq.description.lower())
    ]

    matching_users = [
        {"id": u.id, "full_name": u.full_name}
        for u in db.users.values()
        if term in u.full_name.lower()
    ]

    matching_reviews = [
        {"id": r.id, "equipment_id": r.equipment_id, "rating": r.rating, "comment": r.comment}
        for r in db.reviews.values()
        if term in r.comment.lower()
    ]

    return {
        "query": q,
        "categories": matching_categories,
        "equipment": matching_equipment,
        "users": matching_users,
        "reviews": matching_reviews,
    }
