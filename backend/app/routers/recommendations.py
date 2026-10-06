from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import optional_user, require_roles
from app.db.session import get_db
from app.models import Role, User
from app.schemas.catalog import InterestsIn, PublicProductOut, RecommendedProductOut
from app.services import recommendations as svc

router = APIRouter(tags=["recommendations"])
buyer_only = require_roles(Role.buyer)


@router.get("/me/interests")
def my_interests(user: User = Depends(buyer_only), db: Session = Depends(get_db)):
    return {"category_ids": svc.get_interests(db, user)}


@router.put("/me/interests")
def save_interests(data: InterestsIn, user: User = Depends(buyer_only), db: Session = Depends(get_db)):
    return {"category_ids": svc.set_interests(db, user, data.category_ids)}


@router.get("/recommendations", response_model=list[RecommendedProductOut])
def recommendations(limit: int = Query(8, ge=1, le=24), user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    """Personalised for signed-in buyers (interests + past orders); popular products for everyone else."""
    who = user if user is not None and user.role == Role.buyer else None
    return [
        RecommendedProductOut.model_validate(p).model_copy(update={"seller_name": shop, "district": district, "reason": reason, "match": match})
        for p, shop, district, reason, match in svc.recommend(db, who, limit)
    ]


@router.get("/products/{product_id}/similar", response_model=list[PublicProductOut])
def similar(product_id: int, limit: int = Query(4, ge=1, le=12), db: Session = Depends(get_db)):
    return [
        PublicProductOut.model_validate(p).model_copy(update={"seller_name": shop, "district": district})
        for p, shop, district in svc.similar(db, product_id, limit)
    ]
