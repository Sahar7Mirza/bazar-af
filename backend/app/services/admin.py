from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError, Conflict, NotFound
from app.models import AuditLog, Order, OrderStatus, Product, RefreshToken, Role, SellerProfile, SellerStatus, User
from app.services import audit


def users_stmt(role: str | None, q: str | None) -> Select:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == Role(role))
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%") | User.full_name.ilike(f"%{q}%"))
    return stmt.order_by(User.id)


def set_active(db: Session, admin: User, uid: int, active: bool) -> User:
    u = db.get(User, uid)
    if not u:
        raise NotFound("User not found")
    if u.id == admin.id:
        raise AppError("You cannot deactivate your own account", code="self_action", status_code=409)
    u.is_active = active
    if not active:
        db.execute(update(RefreshToken).where(RefreshToken.user_id == uid, RefreshToken.revoked_at.is_(None)).values(revoked_at=datetime.now(UTC)))
    audit.record(db, "user.activate" if active else "user.deactivate", actor_id=admin.id, entity_type="user", entity_id=uid)
    db.commit()
    return u


def sellers_stmt(status: str | None) -> Select:
    stmt = select(SellerProfile)
    if status:
        stmt = stmt.where(SellerProfile.status == SellerStatus(status))
    return stmt.order_by(SellerProfile.id)


def review_seller(db: Session, admin: User, sid: int, new: SellerStatus, note: str | None) -> SellerProfile:
    sp = db.get(SellerProfile, sid)
    if not sp:
        raise NotFound("Seller not found")
    if sp.status == new:
        raise Conflict(f"Seller is already {new.value}", code="illegal_transition")
    old = sp.status.value
    sp.status, sp.review_note, sp.reviewed_by, sp.reviewed_at = new, note, admin.id, datetime.now(UTC)
    audit.record(db, f"seller.{new.value}", actor_id=admin.id, entity_type="seller", entity_id=sid, detail={"from": old})
    db.commit()
    return sp


def hide_product(db: Session, admin: User, pid: int, hidden: bool) -> Product:
    p = db.get(Product, pid)
    if not p or p.deleted_at:
        raise NotFound("Product not found")
    p.hidden_by_admin = hidden
    audit.record(db, "product.admin_hide" if hidden else "product.admin_unhide", actor_id=admin.id, entity_type="product", entity_id=pid)
    db.commit()
    return p


def orders_stmt(status: str | None) -> Select:
    from sqlalchemy.orm import selectinload

    stmt = select(Order).options(selectinload(Order.items))
    if status:
        stmt = stmt.where(Order.status == OrderStatus(status))
    return stmt.order_by(Order.id.desc())


def audit_stmt(action: str | None) -> Select:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    return stmt.order_by(AuditLog.id.desc())


def stats(db: Session) -> dict:
    cnt = lambda q: db.scalar(q) or 0  # noqa: E731
    by_role = dict(db.execute(select(User.role, func.count()).group_by(User.role)).all())
    by_status = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    by_pref = dict(db.execute(select(Order.payment_preference, func.count()).group_by(Order.payment_preference)).all())
    by_provider = dict(
        db.execute(
            select(Order.mobile_money_provider, func.count()).where(Order.mobile_money_provider.is_not(None)).group_by(Order.mobile_money_provider)
        ).all()
    )
    return {
        "users": {k.value: v for k, v in by_role.items()},
        "sellers_pending": cnt(select(func.count()).select_from(SellerProfile).where(SellerProfile.status == SellerStatus.pending)),
        "sellers_approved": cnt(select(func.count()).select_from(SellerProfile).where(SellerProfile.status == SellerStatus.approved)),
        "products_active": cnt(select(func.count()).select_from(Product).where(Product.deleted_at.is_(None))),
        "orders": {k.value: v for k, v in by_status.items()},
        "orders_total": sum(by_status.values()),
        "payment_preference": {k.value: v for k, v in by_pref.items()},
        "mobile_money_providers": by_provider,
        "total_value_afn": str(db.scalar(select(func.coalesce(func.sum(Order.total_afn), 0)).where(Order.status != OrderStatus.cancelled))),
    }
