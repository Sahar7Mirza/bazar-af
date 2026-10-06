from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.db.session import get_db
from app.models import Role
from app.services import research as svc

router = APIRouter(tags=["research"])
admin_only = require_roles(Role.admin)


@router.get("/research/summary")
def public_summary(response: Response, db: Session = Depends(get_db)):
    """Open to everyone: anonymous totals only, and groups with fewer than 5 orders are left out."""
    response.headers["Cache-Control"] = "public, max-age=30"
    return svc.summary(db, svc.PUBLIC_MIN_CELL)


@router.get("/admin/research/summary", dependencies=[Depends(admin_only)])
def admin_summary(db: Session = Depends(get_db)):
    return svc.summary(db, 1)


@router.get("/admin/research/export.csv", dependencies=[Depends(admin_only)])
def export(db: Session = Depends(get_db)):
    return Response(svc.export_csv(db), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=bazar_orders_anonymised.csv"})
