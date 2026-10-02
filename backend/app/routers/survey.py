from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics import stats as S
from app.core.deps import client_ip, require_roles
from app.core.ratelimit import survey_limiter
from app.db.session import get_db
from app.models import Category, Order, OrderItem, OrderStatus, Product, Role, SellerProfile
from app.schemas.survey import ResponseIn
from app.services import survey as svc

public = APIRouter(prefix="/survey", tags=["survey"])
admin = APIRouter(prefix="/admin", tags=["research"], dependencies=[Depends(require_roles(Role.admin))])


@public.get("")
def questionnaire(db: Session = Depends(get_db)):
    return [
        {"id": q.id, "construct": q.construct, "code": q.code, "text_en": q.text_en, "text_fa": q.text_fa, "position": q.position}
        for q in svc.active_questions(db)
    ]


@public.post("/responses", status_code=201)
def submit(data: ResponseIn, request: Request, db: Session = Depends(get_db)):
    survey_limiter.check(client_ip(request) or "unknown")  # the IP is used only for rate limiting and is never stored with the answers
    r = svc.submit(db, data)
    return {"id": r.id, "message": "Thank you for taking part."}


Filter = dict(respondent_type=Query(None, pattern="^(seller|buyer|other)$"), district=Query(None, max_length=40))


@admin.get("/research/summary")
def summary(db: Session = Depends(get_db)):
    return svc.summary(db)


@admin.get("/research/descriptives")
def descriptives(respondent_type: str | None = Filter["respondent_type"], district: str | None = Filter["district"], db: Session = Depends(get_db)):
    _, scores, _ = svc.load(db, respondent_type, district)
    return {"n": int(len(scores)), "items": S.descriptives(scores) if not scores.empty else []}


@admin.get("/research/reliability")
def reliability(respondent_type: str | None = Filter["respondent_type"], district: str | None = Filter["district"], db: Session = Depends(get_db)):
    items, _, ic = svc.load(db, respondent_type, district)
    return {"n": int(len(items)), "items": S.reliability(items, ic) if not items.empty else []}


@admin.get("/research/correlations")
def correlations(respondent_type: str | None = Filter["respondent_type"], district: str | None = Filter["district"], db: Session = Depends(get_db)):
    _, scores, _ = svc.load(db, respondent_type, district)
    if len(scores) < 3:
        return {"ready": False, "n": int(len(scores))}
    return {"ready": True, "n": int(len(scores)), **S.correlations(scores)}


@admin.get("/research/regression")
def regression(respondent_type: str | None = Filter["respondent_type"], district: str | None = Filter["district"], db: Session = Depends(get_db)):
    _, scores, _ = svc.load(db, respondent_type, district)
    if scores.empty or "WA" not in scores:
        return {"ready": False, "n": 0, "min_n": S.MIN_N_REGRESSION}
    return S.regression(scores)


@admin.get("/research/groups")
def groups(
    by: Literal["uses_mobile_money", "respondent_type", "gender", "age_band", "district"] = "uses_mobile_money", db: Session = Depends(get_db)
):
    return {"by": by, "result": svc.group_table(db, by)}


@admin.get("/research/export.csv")
def export(db: Session = Depends(get_db)):
    return Response(svc.export_csv(db), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=survey_responses.csv"})


@admin.get("/analytics/marketplace")
def marketplace(db: Session = Depends(get_db)):
    live = Order.status != OrderStatus.cancelled
    pref = dict(db.execute(select(Order.payment_preference, func.count()).where(live).group_by(Order.payment_preference)).all())
    prov = dict(
        db.execute(
            select(Order.mobile_money_provider, func.count())
            .where(live, Order.mobile_money_provider.is_not(None))
            .group_by(Order.mobile_money_provider)
        ).all()
    )
    dist = db.execute(
        select(SellerProfile.district, Order.payment_preference, func.count())
        .join(SellerProfile, SellerProfile.id == Order.seller_id)
        .where(live)
        .group_by(SellerProfile.district, Order.payment_preference)
    ).all()
    cat = db.execute(
        select(Category.name, Order.payment_preference, func.count(func.distinct(Order.id)))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .join(Category, Category.id == Product.category_id)
        .where(live)
        .group_by(Category.name, Order.payment_preference)
    ).all()
    buyers_total = db.scalar(select(func.count(func.distinct(Order.buyer_id))).where(live)) or 0
    buyers_mm = db.scalar(select(func.count(func.distinct(Order.buyer_id))).where(live, Order.payment_preference == "mobile_money")) or 0
    week = func.date_trunc("week", Order.created_at)
    weekly_rows = db.execute(
        select(week, Order.payment_preference, func.count()).where(live).group_by(week, Order.payment_preference).order_by(week)
    ).all()
    weeks: dict[str, dict[str, int]] = {}
    for w, p, n in weekly_rows:
        weeks.setdefault(w.date().isoformat(), {"cash": 0, "mobile_money": 0})[getattr(p, "value", p)] = n
    weekly = [{"week": k, **v, "total": v["cash"] + v["mobile_money"]} for k, v in list(weeks.items())[-12:]]
    pref = {getattr(k, "value", k): v for k, v in pref.items()}
    total = sum(pref.values())
    mm = pref.get("mobile_money", 0)

    def table(rows, small=5):
        out = {}
        for k, p, n in rows:
            out.setdefault(k or "Unknown", {"cash": 0, "mobile_money": 0})[getattr(p, "value", p)] = n
        return [{"name": k, **v, "total": v["cash"] + v["mobile_money"]} for k, v in sorted(out.items()) if v["cash"] + v["mobile_money"] >= small]

    return {
        "orders": total,
        "preference": pref,
        "mobile_money_share_pct": round(mm / total * 100, 1) if total else 0,
        "providers": prov,
        "buyers": {"total": buyers_total, "mobile_money": buyers_mm, "share_pct": round(buyers_mm / buyers_total * 100, 1) if buyers_total else 0},
        "weekly": weekly,
        "by_district": table(dist),
        "by_category": table(cat),
    }
