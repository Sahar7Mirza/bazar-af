from typing import Literal

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import client_ip, current_user, require_roles
from app.core.pagination import PageParams, envelope, paginate
from app.db.session import get_db
from app.models import Role, User
from app.schemas.catalog import CancelIn, OrderIn, OrderOut, OrderStatusIn
from app.services import orders as svc

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create(data: OrderIn, request: Request, user: User = Depends(require_roles(Role.buyer)), db: Session = Depends(get_db)):
    """Records the order and the buyer's *simulated* payment preference. No money moves."""
    return svc.create_order(db, user, data, ip=client_ip(request))


@router.get("")
def list_mine(
    status: Literal["pending", "confirmed", "ready", "completed", "cancelled"] | None = None,
    params: PageParams = Depends(),
    user: User = Depends(require_roles(Role.buyer, Role.seller)),
    db: Session = Depends(get_db),
):
    rows, total = paginate(db, svc.list_stmt(db, user, status), params)
    return envelope([OrderOut.model_validate(r) for r in rows], total, params)


@router.get("/{order_id}", response_model=OrderOut)
def get(order_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.get_order(db, user, order_id)


@router.post("/{order_id}/status", response_model=OrderOut)
def set_status(order_id: int, data: OrderStatusIn, user: User = Depends(require_roles(Role.seller)), db: Session = Depends(get_db)):
    return svc.advance(db, user, order_id, data.status, data.pickup_in_minutes)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel(order_id: int, data: CancelIn, user: User = Depends(require_roles(Role.buyer, Role.seller)), db: Session = Depends(get_db)):
    return svc.cancel(db, user, order_id, data.reason)
