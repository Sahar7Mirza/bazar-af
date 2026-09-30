import re
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, Conflict, Forbidden, NotFound
from app.models import Category, Product, ProductStatus, SellerProfile, SellerStatus, User
from app.schemas.catalog import CategoryIn, CategoryPatch, ProductIn, ProductPatch, SellerProfileIn
from app.services import audit


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "category"


# ---- categories
def create_category(db: Session, data: CategoryIn, actor: User) -> Category:
    slug = slugify(data.name)
    if db.scalar(select(Category.id).where((Category.slug == slug) | (Category.name == data.name))):
        raise Conflict("Category already exists", code="category_exists")
    c = Category(name=data.name.strip(), slug=slug, is_active=data.is_active)
    db.add(c)
    db.flush()
    audit.record(db, "category.create", actor_id=actor.id, entity_type="category", entity_id=c.id)
    db.commit()
    return c


def update_category(db: Session, cid: int, data: CategoryPatch, actor: User) -> Category:
    c = db.get(Category, cid) or _missing("Category")
    if data.name is not None:
        slug = slugify(data.name)
        if db.scalar(select(Category.id).where(((Category.slug == slug) | (Category.name == data.name)) & (Category.id != cid))):
            raise Conflict("Category already exists", code="category_exists")
        c.name, c.slug = data.name.strip(), slug
    if data.is_active is not None:
        c.is_active = data.is_active
    audit.record(db, "category.update", actor_id=actor.id, entity_type="category", entity_id=cid)
    db.commit()
    return c


def _missing(what: str):
    raise NotFound(f"{what} not found")


def _check_category(db: Session, category_id: int | None):
    if category_id is not None and not db.scalar(select(Category.id).where(Category.id == category_id, Category.is_active)):
        raise AppError(
            "Unknown category",
            code="validation_error",
            status_code=422,
            details=[{"field": "category_id", "message": "Unknown or inactive category"}],
        )


# ---- seller profile
def my_profile(db: Session, user: User) -> SellerProfile:
    sp = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if not sp:
        raise NotFound("Seller profile not found")
    return sp


def update_profile(db: Session, user: User, data: SellerProfileIn) -> SellerProfile:
    sp = my_profile(db, user)
    _check_category(db, data.category_id)
    for k, v in data.model_dump().items():
        setattr(sp, k, v)
    audit.record(db, "seller.profile_update", actor_id=user.id, entity_type="seller", entity_id=sp.id)
    db.commit()
    return sp


def public_seller(db: Session, sid: int) -> SellerProfile:
    sp = db.get(SellerProfile, sid)
    if not sp or sp.status != SellerStatus.approved:
        raise NotFound("Seller not found")
    return sp


# ---- products
def visible_products() -> Select:
    return (
        select(Product, SellerProfile.business_name, SellerProfile.district)
        .join(SellerProfile, SellerProfile.id == Product.seller_id)
        .where(
            Product.status == ProductStatus.active,
            Product.deleted_at.is_(None),
            Product.hidden_by_admin.is_(False),
            SellerProfile.status == SellerStatus.approved,
        )
    )


SORTS = {"created_at": Product.created_at, "price": Product.price_afn, "name": Product.name}


def search_stmt(q=None, category_id=None, district=None, min_price=None, max_price=None, seller_id=None, sort="created_at", order="desc") -> Select:
    stmt = visible_products()
    if q:
        esc = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{esc}%"
        stmt = stmt.where(Product.name.ilike(like, escape="\\") | Product.description.ilike(like, escape="\\"))
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if district:
        stmt = stmt.where(SellerProfile.district == district)
    if seller_id:
        stmt = stmt.where(Product.seller_id == seller_id)
    if min_price is not None:
        stmt = stmt.where(Product.price_afn >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price_afn <= max_price)
    col = SORTS.get(sort, Product.created_at)
    return stmt.order_by(col.asc() if order == "asc" else col.desc(), Product.id.desc())


def public_product(db: Session, pid: int):
    row = db.execute(visible_products().where(Product.id == pid)).first()
    if not row:
        raise NotFound("Product not found")
    return row


def _approved_profile(db: Session, user: User) -> SellerProfile:
    sp = my_profile(db, user)
    if sp.status != SellerStatus.approved:
        raise Forbidden("Your seller account is not approved yet", code="seller_not_approved")
    return sp


def _own_product(db: Session, user: User, pid: int) -> Product:
    sp = my_profile(db, user)
    p = db.scalar(select(Product).where(Product.id == pid, Product.seller_id == sp.id, Product.deleted_at.is_(None)))
    if not p:
        raise NotFound("Product not found")  # 404, not 403: don't reveal other sellers' products
    return p


def create_product(db: Session, user: User, data: ProductIn) -> Product:
    sp = _approved_profile(db, user)
    _check_category(db, data.category_id)
    p = Product(seller_id=sp.id, status=ProductStatus(data.status), **data.model_dump(exclude={"status"}))
    db.add(p)
    db.flush()
    audit.record(db, "product.create", actor_id=user.id, entity_type="product", entity_id=p.id)
    db.commit()
    return p


def update_product(db: Session, user: User, pid: int, data: ProductPatch) -> Product:
    p = _own_product(db, user, pid)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _check_category(db, changes["category_id"])
    if changes.get("status") == "active" and p.hidden_by_admin:
        raise Forbidden("This product was hidden by an administrator", code="hidden_by_admin")
    for k, v in changes.items():
        setattr(p, k, ProductStatus(v) if k == "status" else v)
    audit.record(db, "product.update", actor_id=user.id, entity_type="product", entity_id=p.id, detail={"fields": sorted(changes)})
    db.commit()
    return p


def delete_product(db: Session, user: User, pid: int) -> None:
    p = _own_product(db, user, pid)
    p.deleted_at = datetime.now(UTC)  # soft delete keeps order history intact
    audit.record(db, "product.delete", actor_id=user.id, entity_type="product", entity_id=p.id)
    db.commit()


def my_products_stmt(db: Session, user: User, q: str | None = None) -> Select:
    sp = my_profile(db, user)
    stmt = select(Product).where(Product.seller_id == sp.id, Product.deleted_at.is_(None))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    return stmt.order_by(Product.id.desc())


def dec(x) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"))


def count_active(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(visible_products().subquery())) or 0
