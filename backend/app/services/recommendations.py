"""Rule-based recommendations: easy to explain in a report and needs no training data.

Score = interest match (+3) + category the buyer has ordered from before (+2) + popularity (0..1) + freshness (0..0.5),
minus 1 if the buyer already ordered this exact product. The `reason` shown to the buyer names the strongest signal.
"""

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Category, Notification, Order, OrderItem, OrderStatus, Product, Role, User, UserInterest
from app.services import catalog

MAX_INTERESTS = 8
POOL = 300


def get_interests(db: Session, user: User) -> list[int]:
    return list(db.scalars(select(UserInterest.category_id).where(UserInterest.user_id == user.id).order_by(UserInterest.category_id)))


def set_interests(db: Session, user: User, category_ids: list[int]) -> list[int]:
    ids = sorted(set(category_ids))
    if ids:
        valid = set(db.scalars(select(Category.id).where(Category.id.in_(ids), Category.is_active.is_(True))))
        bad = [i for i in ids if i not in valid]
        if bad:
            raise AppError(
                "Unknown category",
                code="validation_error",
                status_code=422,
                details=[{"field": "category_ids", "message": f"Unknown category: {bad[0]}"}],
            )
    db.execute(delete(UserInterest).where(UserInterest.user_id == user.id))
    db.add_all(UserInterest(user_id=user.id, category_id=i) for i in ids)
    db.commit()
    return ids


def _popularity(db: Session) -> dict[int, int]:
    rows = db.execute(
        select(OrderItem.product_id, func.count())
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.status != OrderStatus.cancelled)
        .group_by(OrderItem.product_id)
    ).all()
    return {pid: n for pid, n in rows}


MAX_SCORE = 6.5  # 3 interest + 2 ordered category + 1 popularity + 0.5 freshness


def recommend(db: Session, user: User | None, limit: int = 8) -> list[tuple[Product, str, str | None, str, int]]:
    """Returns (product, seller_name, district, reason, match_percent) tuples, best first."""
    pool = db.execute(catalog.visible_products().where(Product.stock_qty > 0).order_by(Product.id.desc()).limit(POOL)).all()
    if not pool:
        return []
    names = {c.id: c.name for c in db.scalars(select(Category))}
    pop = _popularity(db)
    top = max(pop.values(), default=1)
    interests: set[int] = set()
    ordered_cats: set[int] = set()
    ordered_products: set[int] = set()
    if user is not None:
        interests = set(get_interests(db, user))
        for pid, cid in db.execute(
            select(OrderItem.product_id, Product.category_id)
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Order.buyer_id == user.id, Order.status != OrderStatus.cancelled)
        ).all():
            ordered_products.add(pid)
            if cid:
                ordered_cats.add(cid)
    newest = max(p.id for p, _, _ in pool)
    scored = []
    for p, shop, district in pool:
        score = pop.get(p.id, 0) / top + 0.5 * (p.id / newest)
        reason = "Popular in Kabul"
        if p.category_id in ordered_cats:
            score += 2
            reason = f"Because you ordered {names.get(p.category_id, 'this category')} before"
        if p.category_id in interests:
            score += 3
            reason = f"Matches your interest in {names.get(p.category_id, 'this category')}"
        if p.id in ordered_products:
            score -= 1
        scored.append((score, p.id, p, shop, district, reason))
    scored.sort(key=lambda t: (-t[0], -t[1]))
    return [(p, shop, district, reason, max(0, min(100, round(sc / MAX_SCORE * 100)))) for sc, _, p, shop, district, reason in scored[:limit]]


def similar(db: Session, product_id: int, limit: int = 4) -> list[tuple[Product, str, str | None]]:
    base, _, _ = catalog.public_product(db, product_id)
    pop = _popularity(db)
    rows = db.execute(
        catalog.visible_products().where(Product.id != base.id, Product.stock_qty > 0, Product.category_id == base.category_id).limit(POOL)
    ).all()
    rows.sort(key=lambda r: (-pop.get(r[0].id, 0), -r[0].id))
    out = list(rows[:limit])
    if len(out) < limit:  # not enough in the same category: top up with other popular products
        seen = {r[0].id for r in out} | {base.id}
        more = db.execute(catalog.visible_products().where(Product.id.not_in(seen), Product.stock_qty > 0).limit(POOL)).all()
        more.sort(key=lambda r: (-pop.get(r[0].id, 0), -r[0].id))
        out += more[: limit - len(out)]
    return out


def notify_new_product(db: Session, product: Product, shop: str) -> int:
    """Tell buyers who follow this product's category that something new is available. Called inside the caller's transaction."""
    if product.category_id is None:
        return 0
    uids = list(
        db.scalars(
            select(UserInterest.user_id)
            .join(User, User.id == UserInterest.user_id)
            .where(UserInterest.category_id == product.category_id, User.role == Role.buyer, User.is_active.is_(True))
            .limit(500)
        )
    )
    cat = db.get(Category, product.category_id)
    price = f"{product.price_afn:,.0f} AFN / {product.unit}"
    for uid in uids:
        db.add(
            Notification(
                user_id=uid,
                product_id=product.id,
                kind="new_product",
                title=f"New in {cat.name if cat else 'your interests'}",
                message=f"{shop} just listed {product.name} for {price}.",
                created_at=datetime.now(UTC),
            )
        )
    return len(uids)
