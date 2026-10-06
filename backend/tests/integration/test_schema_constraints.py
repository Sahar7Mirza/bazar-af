"""The database itself enforces the project's hard rules, independent of application code."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Order,
    PaymentPreference,
    Role,
    SellerProfile,
    User,
)


def _seller(db):
    u = User(email="s@x.af", password_hash="h", full_name="S", role=Role.seller)
    db.add(u)
    db.flush()
    sp = SellerProfile(user_id=u.id, business_name="Shop")
    db.add(sp)
    b = User(email="b@x.af", password_hash="h", full_name="B", role=Role.buyer)
    db.add(b)
    db.flush()
    return b, sp


def test_order_cannot_be_marked_paid(db):
    b, sp = _seller(db)
    db.add(Order(buyer_id=b.id, seller_id=sp.id, payment_preference=PaymentPreference.cash, payment_status="paid", total_afn=10))
    with pytest.raises(IntegrityError):
        db.commit()


def test_provider_only_with_mobile_money(db):
    b, sp = _seller(db)
    db.add(Order(buyer_id=b.id, seller_id=sp.id, payment_preference=PaymentPreference.cash, mobile_money_provider="M-Paisa", total_afn=10))
    with pytest.raises(IntegrityError):
        db.commit()


def test_valid_order_and_audit_timestamps(db):
    b, sp = _seller(db)
    o = Order(buyer_id=b.id, seller_id=sp.id, payment_preference=PaymentPreference.mobile_money, mobile_money_provider="M-Paisa", total_afn=10)
    db.add(o)
    db.commit()
    assert o.payment_status == "not_processed" and o.created_at and o.updated_at


def test_email_unique(db):
    db.add(User(email="a@x.af", password_hash="h", full_name="A", role=Role.buyer))
    db.commit()
    db.add(User(email="a@x.af", password_hash="h", full_name="A2", role=Role.buyer))
    with pytest.raises(IntegrityError):
        db.commit()
