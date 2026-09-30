from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PROVIDERS = ("M-Paisa", "HesabPay", "Afghan Wireless Mobile Money", "MoneyPay", "Other")
DISTRICTS = [f"PD{i}" for i in range(1, 23)] + ["Other"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CategoryIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    is_active: bool = True


class CategoryPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    is_active: bool | None = None


class CategoryOut(ORM):
    id: int
    name: str
    slug: str
    is_active: bool


class SellerProfileIn(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    category_id: int | None = None
    description: str | None = Field(default=None, max_length=2000)
    district: Literal[tuple(DISTRICTS)] | None = None  # type: ignore[valid-type]
    address_note: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    opening_hours: str | None = Field(default=None, max_length=120)


class SellerOut(ORM):
    id: int
    business_name: str
    category_id: int | None
    description: str | None
    district: str | None
    address_note: str | None
    phone: str | None
    opening_hours: str | None
    status: str
    review_note: str | None = None
    created_at: datetime


class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int | None = None
    price_afn: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    unit: str = Field(default="piece", min_length=1, max_length=30)
    stock_qty: int = Field(default=0, ge=0, le=1_000_000)
    status: Literal["active", "hidden"] = "active"


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    category_id: int | None = None
    price_afn: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    stock_qty: int | None = Field(default=None, ge=0, le=1_000_000)
    status: Literal["active", "hidden"] | None = None


class ProductOut(ORM):
    id: int
    seller_id: int
    category_id: int | None
    name: str
    description: str | None
    price_afn: Decimal
    unit: str
    stock_qty: int
    status: str
    hidden_by_admin: bool
    created_at: datetime
    updated_at: datetime


class PublicProductOut(ProductOut):
    seller_name: str | None = None
    district: str | None = None


class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=10_000)


class OrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    payment_preference: Literal["cash", "mobile_money"]
    mobile_money_provider: str | None = None
    buyer_note: str | None = Field(default=None, max_length=300)

    @field_validator("mobile_money_provider")
    @classmethod
    def known(cls, v):
        if v is not None and v not in PROVIDERS:
            raise ValueError(f"Provider must be one of: {', '.join(PROVIDERS)}")
        return v


class OrderItemOut(ORM):
    product_id: int
    product_name: str
    unit_price_afn: Decimal
    quantity: int
    line_total_afn: Decimal


class OrderOut(ORM):
    id: int
    buyer_id: int
    seller_id: int
    status: str
    payment_preference: str
    mobile_money_provider: str | None
    payment_status: str
    total_afn: Decimal
    buyer_note: str | None
    cancel_reason: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]


class OrderStatusIn(BaseModel):
    status: Literal["confirmed", "ready", "completed"]


class CancelIn(BaseModel):
    reason: str | None = Field(default=None, max_length=300)


class ReviewIn(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class UserPatch(BaseModel):
    is_active: bool
