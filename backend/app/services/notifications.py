from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Notification, Order, OrderStatus, SellerProfile, User


def human_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} minutes"
    if minutes < 1440:
        h, m = divmod(minutes, 60)
        return f"{h} hour{'s' if h != 1 else ''}" + (f" {m} minutes" if m else "")
    d = round(minutes / 1440)
    return f"{d} day{'s' if d != 1 else ''}"


def notify(db: Session, user_id: int, order: Order, kind: str, title: str, message: str) -> Notification:
    n = Notification(user_id=user_id, order_id=order.id, kind=kind, title=title, message=message[:400])
    db.add(n)
    return n  # committed together with the order change


def new_order_for_seller(db: Session, order: Order, seller_user_id: int, buyer_name: str, items: int, pref_label: str) -> None:
    """Tell the shop owner a new order arrived. It stays unread until the seller confirms or cancels it (see resolve_new_order)."""
    notify(
        db,
        seller_user_id,
        order,
        "new_order",
        f"New order #{order.id}",
        f"{buyer_name} ordered {items} item{'s' if items != 1 else ''} for {order.total_afn:,.0f} AFN ({pref_label}). "
        "Confirm it and give a pickup time.",
    )


def resolve_new_order(db: Session, order_id: int) -> None:
    """The seller acted on the order, so its 'new order' alert is no longer waiting for them."""
    db.execute(
        update(Notification)
        .where(Notification.order_id == order_id, Notification.kind == "new_order", Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )


def order_confirmed(db: Session, order: Order, shop: str, minutes: int) -> None:
    notify(
        db,
        order.buyer_id,
        order,
        "order_confirmed",
        f"Order #{order.id} confirmed",
        f"{shop} confirmed your order #{order.id}. Estimated time until pickup: about {human_duration(minutes)}.",
    )


def order_ready(db: Session, order: Order, shop: str) -> None:
    notify(db, order.buyer_id, order, "order_ready", f"Order #{order.id} is ready", f"Your order #{order.id} is ready for pick up at {shop}.")


def order_cancelled_by_seller(db: Session, order: Order, shop: str, reason: str | None) -> None:
    extra = f" Reason: {reason}" if reason else ""
    notify(db, order.buyer_id, order, "order_cancelled", f"Order #{order.id} cancelled", f"{shop} cancelled your order #{order.id}.{extra}")


def list_stmt(user: User, unread_only: bool = False) -> Select:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return stmt.order_by(Notification.id.desc())


def unread_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))) or 0


def mark_read(db: Session, user: User, nid: int) -> Notification:
    n = db.scalar(select(Notification).where(Notification.id == nid, Notification.user_id == user.id))
    if not n:
        raise NotFound("Notification not found")
    if n.read_at is None:
        n.read_at = datetime.now(UTC)
        db.commit()
    return n


def mark_all_read(db: Session, user: User) -> int:
    res = db.execute(update(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None)).values(read_at=datetime.now(UTC)))
    db.commit()
    return res.rowcount or 0


def live_state(db: Session, user: User) -> dict:
    """Small payload the app polls every few seconds: unread count, the newest unread alert, and (sellers) orders still waiting for action."""
    latest = db.scalar(
        select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None)).order_by(Notification.id.desc()).limit(1)
    )
    out: dict = {
        "unread": unread_count(db, user),
        "latest": {"id": latest.id, "kind": latest.kind, "title": latest.title, "message": latest.message, "order_id": latest.order_id}
        if latest
        else None,
    }
    if user.role.value == "seller":
        sp = db.scalar(select(SellerProfile.id).where(SellerProfile.user_id == user.id))
        out["pending_orders"] = (
            db.scalar(select(func.count()).select_from(Order).where(Order.seller_id == (sp or -1), Order.status == OrderStatus.pending)) or 0
        )
    return out
