from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.pagination import PageParams, envelope, paginate
from app.db.session import get_db
from app.models import Role, SellerStatus, User
from app.schemas.auth import UserOut
from app.schemas.catalog import CategoryIn, CategoryOut, CategoryPatch, OrderOut, ProductOut, ReviewIn, SellerOut, UserPatch
from app.services import admin as svc
from app.services import catalog
from app.services import orders as orders_svc

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles(Role.admin))])
admin_user = require_roles(Role.admin)


@router.get("/users")
def users(
    role: Literal["buyer", "seller", "admin"] | None = None,
    q: str | None = Query(None, max_length=100),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    rows, total = paginate(db, svc.users_stmt(role, q), params)
    return envelope([UserOut.model_validate(r) for r in rows], total, params)


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(user_id: int, data: UserPatch, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return svc.set_active(db, admin, user_id, data.is_active)


@router.get("/sellers")
def sellers(
    status: Literal["pending", "approved", "rejected", "suspended"] | None = None, params: PageParams = Depends(), db: Session = Depends(get_db)
):
    rows, total = paginate(db, svc.sellers_stmt(status), params)
    return envelope([SellerOut.model_validate(r) for r in rows], total, params)


def _review(new: SellerStatus):
    def handler(seller_id: int, data: ReviewIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
        return svc.review_seller(db, admin, seller_id, new, data.note)

    return handler


for _name, _st in (("approve", SellerStatus.approved), ("reject", SellerStatus.rejected), ("suspend", SellerStatus.suspended)):
    router.add_api_route(f"/sellers/{{seller_id}}/{_name}", _review(_st), methods=["POST"], response_model=SellerOut, name=f"seller_{_name}")


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return catalog.create_category(db, data, admin)


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def patch_category(category_id: int, data: CategoryPatch, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return catalog.update_category(db, category_id, data, admin)


@router.post("/products/{product_id}/hide", response_model=ProductOut)
def hide(product_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return svc.hide_product(db, admin, product_id, True)


@router.post("/products/{product_id}/unhide", response_model=ProductOut)
def unhide(product_id: int, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return svc.hide_product(db, admin, product_id, False)


@router.get("/orders")
def orders(
    status: Literal["pending", "confirmed", "ready", "completed", "cancelled"] | None = None,
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    rows, total = paginate(db, svc.orders_stmt(status), params)
    return {**envelope([OrderOut.model_validate(r) for r in rows], total, params), "counts": orders_svc.status_counts(db, svc.orders_stmt(None))}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return svc.stats(db)


@router.get("/audit")
def audit_log(action: str | None = Query(None, max_length=60), params: PageParams = Depends(), db: Session = Depends(get_db)):
    rows, total = paginate(db, svc.audit_stmt(action), params)
    items = [
        {
            "id": r.id,
            "actor_id": r.actor_id,
            "action": r.action,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "detail": r.detail,
            "request_id": r.request_id,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return envelope(items, total, params)
