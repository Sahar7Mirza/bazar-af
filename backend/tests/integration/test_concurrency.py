"""Two buyers race for the last item: row locking must let exactly one win."""

import threading

from fastapi.testclient import TestClient

from app.models import Product, Role
from tests.helpers import make_product, make_seller, make_user, token


def test_no_overselling_under_concurrency(client, db):
    from app.main import app

    _, sp = make_seller(db, "s@x.af")
    p = make_product(db, sp, stock=1)
    heads = []
    for i in range(4):
        make_user(db, f"b{i}@x.af", Role.buyer)
        heads.append(token(client, f"b{i}@x.af"))
    results = []

    def buy(h):
        with TestClient(app, raise_server_exceptions=False) as c:
            results.append(
                c.post("/api/v1/orders", json={"items": [{"product_id": p.id, "quantity": 1}], "payment_preference": "cash"}, headers=h).status_code
            )

    ts = [threading.Thread(target=buy, args=(h,)) for h in heads]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(results) == [201, 409, 409, 409]
    db.expire_all()
    assert db.get(Product, p.id).stock_qty == 0
