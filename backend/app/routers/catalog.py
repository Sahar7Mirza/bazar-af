from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.pagination import PageParams, envelope, paginate
from app.db.session import get_db
from app.models import Category, Role, User
from app.schemas.catalog import CategoryOut, ProductIn, ProductOut, ProductPatch, PublicProductOut, SellerOut, SellerProfileIn
from app.services import catalog as svc

router = APIRouter(tags=["catalog"])
seller_only = require_roles(Role.seller)


@router.get("/categories", response_model=list[CategoryOut])
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).where(Category.is_active).order_by(Category.name)).all()


@router.get("/sellers/me", response_model=SellerOut)
def my_profile(user: User = Depends(seller_only), db: Session = Depends(get_db)):
    return svc.my_profile(db, user)


@router.put("/sellers/me", response_model=SellerOut)
def update_profile(data: SellerProfileIn, user: User = Depends(seller_only), db: Session = Depends(get_db)):
    return svc.update_profile(db, user, data)


@router.get("/sellers/me/products")
def my_products(
    q: str | None = Query(None, max_length=100), params: PageParams = Depends(), user: User = Depends(seller_only), db: Session = Depends(get_db)
):
    rows, total = paginate(db, svc.my_products_stmt(db, user, q), params)
    return envelope([ProductOut.model_validate(r) for r in rows], total, params)


@router.get("/sellers/{seller_id}", response_model=SellerOut)
def public_seller(seller_id: int, db: Session = Depends(get_db)):
    sp = svc.public_seller(db, seller_id)
    return SellerOut.model_validate(sp).model_copy(update={"review_note": None})


@router.get("/products")
def list_products(
    q: str | None = Query(None, max_length=100),
    category_id: int | None = None,
    district: str | None = Query(None, max_length=40),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    seller_id: int | None = None,
    sort: Literal["created_at", "price", "name"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    stmt = svc.search_stmt(q, category_id, district, min_price, max_price, seller_id, sort, order)
    total = db.scalar(select(__import__("sqlalchemy").func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(params.page_size).offset(params.offset)).all()
    items = [PublicProductOut.model_validate(p).model_copy(update={"seller_name": n, "district": d}) for p, n, d in rows]
    return envelope(items, total, params)


@router.get("/products/{product_id}", response_model=PublicProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p, name, district = svc.public_product(db, product_id)
    return PublicProductOut.model_validate(p).model_copy(update={"seller_name": name, "district": district})


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, user: User = Depends(seller_only), db: Session = Depends(get_db)):
    return svc.create_product(db, user, data)


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductPatch, user: User = Depends(seller_only), db: Session = Depends(get_db)):
    return svc.update_product(db, user, product_id, data)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, user: User = Depends(seller_only), db: Session = Depends(get_db)):
    svc.delete_product(db, user, product_id)
    return Response(status_code=204)
