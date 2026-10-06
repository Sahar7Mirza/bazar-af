import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _enum(e):
    return Enum(e, name=e.__name__.lower(), values_callable=lambda x: [m.value for m in x])


class Role(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class SellerStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    suspended = "suspended"


class ProductStatus(str, enum.Enum):
    active = "active"
    hidden = "hidden"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    ready = "ready"
    completed = "completed"
    cancelled = "cancelled"


class PaymentPreference(str, enum.Enum):
    cash = "cash"
    mobile_money = "mobile_money"


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, Timestamps):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(_enum(Role))
    district: Mapped[str | None] = mapped_column(String(40))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    failed_logins: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seller_profile: Mapped["SellerProfile | None"] = relationship(back_populates="user", foreign_keys="SellerProfile.user_id")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailToken(Base):
    """One-time link sent by email (password reset or email verification). Only a hash of the token is stored."""

    __tablename__ = "email_tokens"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # reset | verify
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Category(Base, Timestamps):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class SellerProfile(Base, Timestamps):
    __tablename__ = "seller_profiles"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    business_name: Mapped[str] = mapped_column(String(120))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(String(40), index=True)
    address_note: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    opening_hours: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[SellerStatus] = mapped_column(_enum(SellerStatus), default=SellerStatus.pending, index=True)
    review_note: Mapped[str | None] = mapped_column(String(300))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates="seller_profile", foreign_keys=[user_id])
    category: Mapped[Category | None] = relationship()


class Product(Base, Timestamps):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_afn >= 0", name="ck_price_nonneg"),
        CheckConstraint("stock_qty >= 0", name="ck_stock_nonneg"),
        Index("ix_products_seller_status", "seller_id", "status"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("seller_profiles.id", ondelete="CASCADE"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price_afn: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit: Mapped[str] = mapped_column(String(30), default="piece")
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[ProductStatus] = mapped_column(_enum(ProductStatus), default=ProductStatus.active)
    hidden_by_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seller: Mapped[SellerProfile] = relationship()
    category: Mapped[Category | None] = relationship()


class Order(Base, Timestamps):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("payment_status = 'not_processed'", name="ck_no_real_payment"),
        CheckConstraint("(payment_preference = 'mobile_money') OR mobile_money_provider IS NULL", name="ck_provider_only_mm"),
        Index("ix_orders_buyer_created", "buyer_id", "created_at"),
        Index("ix_orders_seller_status", "seller_id", "status"),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    seller_id: Mapped[int] = mapped_column(ForeignKey("seller_profiles.id"))
    status: Mapped[OrderStatus] = mapped_column(_enum(OrderStatus), default=OrderStatus.pending)
    payment_preference: Mapped[PaymentPreference] = mapped_column(_enum(PaymentPreference))
    mobile_money_provider: Mapped[str | None] = mapped_column(String(40))
    payment_status: Mapped[str] = mapped_column(String(20), default="not_processed", server_default="not_processed")
    total_afn: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    buyer_note: Mapped[str | None] = mapped_column(String(300))
    cancel_reason: Mapped[str | None] = mapped_column(String(300))
    estimated_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # set by the seller when confirming
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, Timestamps):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_qty_pos"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(150))  # snapshot
    unit_price_afn: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # snapshot
    quantity: Mapped[int] = mapped_column(Integer)
    line_total_afn: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    order: Mapped[Order] = relationship(back_populates="items")


class Notification(Base):
    """In-app notification (shown under the bell). Email delivery can be layered on later without changing this table."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_created", "user_id", "created_at"), Index("ix_notifications_user_unread", "user_id", "read_at"))
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(30))  # new_order (to the seller) | order_confirmed | order_ready | order_cancelled | new_product
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(String(400))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserInterest(Base):
    """A category a buyer said they are interested in; drives recommendations and "new in your interests" alerts."""

    __tablename__ = "user_interests"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_created", "created_at"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(40))
    detail: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(INET)
    request_id: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
