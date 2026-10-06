from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.core.pagination import PageParams, envelope, paginate
from app.db.session import get_db
from app.models import User
from app.services import notifications as svc

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_id: int | None
    product_id: int | None
    kind: str
    title: str
    message: str
    read_at: datetime | None
    created_at: datetime


@router.get("")
def list_mine(unread: bool = False, params: PageParams = Depends(), user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows, total = paginate(db, svc.list_stmt(user, unread), params)
    return envelope([NotificationOut.model_validate(r) for r in rows], total, params)


@router.get("/unread-count")
def unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.live_state(db, user)


@router.post("/read-all")
def read_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return {"marked": svc.mark_all_read(db, user)}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_one(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return svc.mark_read(db, user, notification_id)
