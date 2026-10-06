"""Mobile-money adoption research, computed from the Cash / Mobile Money choice buyers make at checkout.

Nothing here touches money: the choice is a stated preference. The same numbers feed the public Research page
(small groups hidden so nobody can be singled out) and the admin page (every group, plus a CSV for the paper)."""

import csv
import io
import math
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Category, Order, OrderItem, OrderStatus, Product, SellerProfile

PUBLIC_MIN_CELL = 5  # a district/category with fewer orders is not shown publicly
MIN_FOR_TEST = 20  # below this many orders a significance test says nothing


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a share (Wilson score), in percent. Honest about small samples."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, centre - half) * 100, 1), round(min(1.0, centre + half) * 100, 1))


def _gamma_q(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x), used for the chi-square p-value (no SciPy needed)."""
    if x <= 0:
        return 1.0
    if x < a + 1:  # series for P, then 1 - P
        term = total = 1.0 / a
        n = a
        for _ in range(500):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-12:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    tiny = 1e-300  # continued fraction for Q
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-12:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi_square(rows: list[tuple[int, int]]) -> dict | None:
    """Do groups differ in their mobile-money share? rows = [(cash, mobile_money), ...]. None when the data is too thin to say."""
    rows = [r for r in rows if r[0] + r[1] > 0]
    total = sum(c + m for c, m in rows)
    if len(rows) < 2 or total < MIN_FOR_TEST:
        return None
    cash_all, mm_all = sum(c for c, _ in rows), sum(m for _, m in rows)
    if cash_all == 0 or mm_all == 0:
        return None
    stat = 0.0
    for c, m in rows:
        n = c + m
        ec, em = n * cash_all / total, n * mm_all / total
        stat += (c - ec) ** 2 / ec + (m - em) ** 2 / em
    df = len(rows) - 1
    p = _gamma_q(df / 2, stat / 2)
    cramers_v = math.sqrt(stat / total)  # 2 columns, so min(r-1, c-1) = 1
    return {"chi2": round(stat, 2), "df": df, "p": round(p, 4), "cramers_v": round(cramers_v, 2), "significant": p < 0.05}


def _live() -> object:
    return Order.status != OrderStatus.cancelled


def _pref(v) -> str:
    return getattr(v, "value", v)


def _table(rows, min_cell: int) -> list[dict]:
    out: dict[str, dict[str, int]] = {}
    for k, p, n in rows:
        out.setdefault(k or "Unknown", {"cash": 0, "mobile_money": 0})[_pref(p)] = n
    res = []
    for name, v in sorted(out.items()):
        total = v["cash"] + v["mobile_money"]
        if total >= min_cell:
            lo, hi = wilson(v["mobile_money"], total)
            res.append({"name": name, **v, "total": total, "share_pct": round(v["mobile_money"] / total * 100, 1), "ci_pct": [lo, hi]})
    return res


def summary(db: Session, min_cell: int = PUBLIC_MIN_CELL) -> dict:
    live = _live()
    pref = {_pref(k): v for k, v in db.execute(select(Order.payment_preference, func.count()).where(live).group_by(Order.payment_preference)).all()}
    total = sum(pref.values())
    mm = pref.get("mobile_money", 0)
    prov = {
        k: n
        for k, n in db.execute(
            select(Order.mobile_money_provider, func.count())
            .where(live, Order.mobile_money_provider.is_not(None))
            .group_by(Order.mobile_money_provider)
        ).all()
    }
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
    weeks: dict[str, dict[str, int]] = {}
    for w, p, n in db.execute(
        select(week, Order.payment_preference, func.count()).where(live).group_by(week, Order.payment_preference).order_by(week)
    ).all():
        weeks.setdefault(w.date().isoformat(), {"cash": 0, "mobile_money": 0})[_pref(p)] = n
    weekly = [{"week": k, **v, "total": v["cash"] + v["mobile_money"]} for k, v in list(weeks.items())[-12:]]
    avg = {
        _pref(p): round(float(a), 0)
        for p, a in db.execute(select(Order.payment_preference, func.avg(Order.total_afn)).where(live).group_by(Order.payment_preference)).all()
    }
    first, last = db.execute(select(func.min(Order.created_at), func.max(Order.created_at)).where(live)).one()
    by_district, by_category = _table(dist, min_cell), _table(cat, min_cell)
    lo, hi = wilson(mm, total)
    return {
        "orders": total,
        "preference": pref,
        "mobile_money_share_pct": round(mm / total * 100, 1) if total else 0,
        "ci_pct": [lo, hi],
        "providers": prov,
        "avg_order_afn": avg,
        "buyers": {"total": buyers_total, "mobile_money": buyers_mm, "share_pct": round(buyers_mm / buyers_total * 100, 1) if buyers_total else 0},
        "weekly": weekly,
        "by_district": by_district,
        "by_category": by_category,
        "tests": {
            "district": chi_square([(r["cash"], r["mobile_money"]) for r in by_district]),
            "category": chi_square([(r["cash"], r["mobile_money"]) for r in by_category]),
        },
        "period": {"from": first.date().isoformat() if first else None, "to": last.date().isoformat() if last else None},
        "min_cell": min_cell,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def export_stmt() -> Select:
    """One row per order with no names, emails or IDs of people: safe to analyse in R / SPSS / Excel for the paper."""
    return (
        select(
            Order.id,
            Order.created_at,
            SellerProfile.district,
            Order.payment_preference,
            Order.mobile_money_provider,
            Order.total_afn,
            Order.status,
            func.count(OrderItem.id).label("lines"),
            func.min(Category.name).label("category"),
        )
        .join(SellerProfile, SellerProfile.id == Order.seller_id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .join(Category, Category.id == Product.category_id)
        .group_by(Order.id, SellerProfile.district)
        .order_by(Order.id)
    )


def export_csv(db: Session) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["order_id", "week", "district", "category", "payment_preference", "mobile_money_provider", "total_afn", "status", "lines"])
    for r in db.execute(export_stmt()).all():
        w.writerow(
            [
                r.id,
                r.created_at.date().isoformat(),
                r.district or "",
                r.category or "",
                _pref(r.payment_preference),
                r.mobile_money_provider or "",
                r.total_afn,
                _pref(r.status),
                r.lines,
            ]
        )
    return buf.getvalue()
