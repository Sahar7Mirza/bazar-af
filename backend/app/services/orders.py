from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError, Conflict, Forbidden, NotFound
from app.models import Order, OrderItem, OrderStatus, PaymentPreference, Product, ProductStatus, Role, SellerProfile, SellerStatus, User
from app.schemas.catalog import OrderIn
from app.services import audit, notifications

# Legal seller-driven transitions. Cancellation is handled separately.
NEXT = {OrderStatus.pending: OrderStatus.confirmed, OrderStatus.confirmed: OrderStatus.ready, OrderStatus.ready: OrderStatus.completed}


def _invalid(field: str, msg: str):
    return AppError(msg, code="validation_error", status_code=422, details=[{"field": field, "message": msg}])


def create_order(db: Session, buyer: User, data: OrderIn, ip: str | None = None) -> Order:
    ids = [i.product_id for i in data.items]
    if len(set(ids)) != len(ids):
        raise _invalid("items", "Each product may appear only once")
    if data.payment_preference == "mobile_money" and not data.mobile_money_provider:
        raise _invalid("mobile_money_provider", "Choose a mobile money provider")
    if data.payment_preference == "cash" and data.mobile_money_provider:
        raise _invalid("mobile_money_provider", "Provider only applies to mobile money")
    # Lock in id order so concurrent orders cannot deadlock or oversell.
    prods = {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update())}
    sellers = set()
    lines = []
    for it in data.items:
        p = prods.get(it.product_id)
        if not p or p.deleted_at or p.status != ProductStatus.active or p.hidden_by_admin:
            raise NotFound(f"Product {it.product_id} is not available", code="product_unavailable")
        sellers.add(p.seller_id)
        lines.append((p, it.quantity))
    if len(sellers) != 1:
        raise _invalid("items", "An order can contain products from one seller only")
    seller = db.get(SellerProfile, next(iter(sellers)))
    if seller.status != SellerStatus.approved:
        raise NotFound("Product is not available", code="product_unavailable")
    if seller.user_id == buyer.id:
        raise Forbidden("You cannot order from your own shop")
    total = Decimal("0")
    order = Order(
        buyer_id=buyer.id,
        seller_id=seller.id,
        status=OrderStatus.pending,
        payment_preference=PaymentPreference(data.payment_preference),
        mobile_money_provider=data.mobile_money_provider,
        buyer_note=data.buyer_note,
        total_afn=0,
    )
    for p, qty in lines:
        if p.stock_qty < qty:
            raise Conflict(
                f"Not enough stock for {p.name} (available: {p.stock_qty})",
                code="insufficient_stock",
                details=[{"product_id": p.id, "available": p.stock_qty}],
            )
        p.stock_qty -= qty
        line = (p.price_afn * qty).quantize(Decimal("0.01"))  # price comes from the DB, never from the client
        total += line
        order.items.append(OrderItem(product_id=p.id, product_name=p.name, unit_price_afn=p.price_afn, quantity=qty, line_total_afn=line))
    order.total_afn = total
    db.add(order)
    db.flush()
    audit.record(
        db,
        "order.create",
        actor_id=buyer.id,
        entity_type="order",
        entity_id=order.id,
        detail={"total_afn": str(total), "payment_preference": data.payment_preference},
        ip=ip,
    )
    db.commit()
    return order


def _with_items(stmt: Select) -> Select:
    return stmt.options(selectinload(Order.items))


def list_stmt(db: Session, user: User, status: str | None = None) -> Select:
    stmt = _with_items(select(Order))
    if user.role == Role.buyer:
        stmt = stmt.where(Order.buyer_id == user.id)
    elif user.role == Role.seller:
        sp = db.scalar(select(SellerProfile.id).where(SellerProfile.user_id == user.id))
        stmt = stmt.where(Order.seller_id == (sp or -1))
    if status:
        stmt = stmt.where(Order.status == OrderStatus(status))
    return stmt.order_by(Order.id.desc())


def status_counts(db: Session, stmt: Select) -> dict[str, int]:
    """Orders per status for an (unfiltered-by-status) listing, so the UI can show chips like "Pending 3"."""
    sub = stmt.order_by(None).subquery()
    got = {str(getattr(st, "value", st)): n for st, n in db.execute(select(sub.c.status, func.count()).group_by(sub.c.status)).all()}
    return {s: got.get(s, 0) for s in ("pending", "confirmed", "ready", "completed", "cancelled")}


def get_order(db: Session, user: User, oid: int, lock: bool = False) -> Order:
    stmt = _with_items(select(Order).where(Order.id == oid))
    if lock:
        stmt = stmt.with_for_update(of=Order)
    o = db.scalar(stmt)
    if not o:
        raise NotFound("Order not found")
    if user.role == Role.admin:
        return o
    if user.role == Role.buyer and o.buyer_id == user.id:
        return o
    if user.role == Role.seller:
        sp = db.scalar(select(SellerProfile.id).where(SellerProfile.user_id == user.id))
        if sp == o.seller_id:
            return o
    raise NotFound("Order not found")  # never reveal someone else's order exists


DEFAULT_PICKUP_MINUTES = 60


def _shop_name(db: Session, o: Order) -> str:
    return db.get(SellerProfile, o.seller_id).business_name


def advance(db: Session, seller: User, oid: int, target: str, pickup_in_minutes: int | None = None) -> Order:
    o = get_order(db, seller, oid, lock=True)
    if NEXT.get(o.status) != OrderStatus(target):
        raise Conflict(f"Cannot move an order from {o.status.value} to {target}", code="illegal_transition")
    before = o.status.value
    o.status = OrderStatus(target)
    if o.status == OrderStatus.confirmed:
        minutes = pickup_in_minutes or DEFAULT_PICKUP_MINUTES
        o.estimated_pickup_at = datetime.now(UTC) + timedelta(minutes=minutes)
        notifications.order_confirmed(db, o, _shop_name(db, o), minutes)
    elif o.status == OrderStatus.ready:
        notifications.order_ready(db, o, _shop_name(db, o))
    audit.record(db, "order.status", actor_id=seller.id, entity_type="order", entity_id=o.id, detail={"from": before, "to": target})
    db.commit()
    return o


def cancel(db: Session, user: User, oid: int, reason: str | None) -> Order:
    o = get_order(db, user, oid, lock=True)
    allowed = {OrderStatus.pending} if user.role == Role.buyer else {OrderStatus.pending, OrderStatus.confirmed, OrderStatus.ready}
    if user.role == Role.admin or o.status not in allowed:
        raise Conflict(f"An order that is {o.status.value} cannot be cancelled by you", code="illegal_transition")
    for it in o.items:  # restore stock
        p = db.get(Product, it.product_id, with_for_update=True)
        p.stock_qty += it.quantity
    o.status, o.cancel_reason = OrderStatus.cancelled, reason
    if user.role == Role.seller:
        notifications.order_cancelled_by_seller(db, o, _shop_name(db, o), reason)
    audit.record(db, "order.cancel", actor_id=user.id, entity_type="order", entity_id=o.id, detail={"by": user.role.value})
    db.commit()
    return o
