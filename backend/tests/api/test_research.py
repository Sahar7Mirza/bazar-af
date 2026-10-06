import math

from app.models import Role
from app.services.research import _gamma_q, chi_square, wilson
from tests.helpers import make_category, make_product, make_seller, make_user, token


def test_wilson_interval_matches_known_values():
    assert wilson(0, 0) == (0.0, 0.0)
    lo, hi = wilson(50, 100)
    assert (lo, hi) == (40.4, 59.6)
    lo, hi = wilson(1, 3)  # tiny sample -> very wide, which is the honest answer
    assert hi - lo > 60


def test_chi_square_p_value_matches_reference():
    assert math.isclose(_gamma_q(0.5, 3.841 / 2), 0.05, abs_tol=2e-3)  # chi2=3.841, df=1  ->  p≈0.05
    assert math.isclose(_gamma_q(1.5, 7.815 / 2), 0.05, abs_tol=2e-3)  # chi2=7.815, df=3  ->  p≈0.05
    t = chi_square([(40, 10), (10, 40)])  # strongly different groups
    assert t["significant"] and t["p"] < 0.001 and t["df"] == 1
    assert chi_square([(25, 25), (25, 25)])["significant"] is False
    assert chi_square([(2, 1), (1, 2)]) is None  # too few orders to test


def _orders(client, db, n_mm, n_cash):
    su, sp = make_seller(db, "s@x.af")
    make_user(db, "b@x.af", Role.buyer)
    make_user(db, "a@x.af", Role.admin)
    p = make_product(db, sp, "Bread", "25.00", 500, category_id=make_category(db, "Food").id)
    h = token(client, "b@x.af")
    for _ in range(n_mm):
        assert (
            client.post(
                "/api/v1/orders",
                json={"items": [{"product_id": p.id, "quantity": 1}], "payment_preference": "mobile_money", "mobile_money_provider": "M-Paisa"},
                headers=h,
            ).status_code
            == 201
        )
    for _ in range(n_cash):
        assert (
            client.post("/api/v1/orders", json={"items": [{"product_id": p.id, "quantity": 1}], "payment_preference": "cash"}, headers=h).status_code
            == 201
        )
    return h


def test_public_summary_needs_no_login_and_hides_small_groups(client, db):
    _orders(client, db, 2, 1)  # 3 orders: below the public minimum of 5 per group
    r = client.get("/api/v1/research/summary")
    assert r.status_code == 200
    d = r.json()
    assert d["orders"] == 3 and d["mobile_money_share_pct"] == 66.7 and d["by_district"] == [] and d["by_category"] == []
    assert "buyer" not in str(d).lower().replace("buyers", "")  # no personal identifiers anywhere in the payload


def test_public_summary_shows_groups_once_big_enough(client, db):
    _orders(client, db, 6, 4)
    d = client.get("/api/v1/research/summary").json()
    assert d["by_district"][0]["name"] == "PD4" and d["by_district"][0]["total"] == 10 and d["by_district"][0]["share_pct"] == 60.0
    assert d["by_category"][0]["name"] == "Food" and d["avg_order_afn"]["cash"] == 25
    assert d["period"]["from"] and d["tests"]["district"] is None  # one group cannot be compared


def test_admin_summary_shows_every_group_and_exports_anonymised_csv(client, db):
    _orders(client, db, 1, 1)
    admin = token(client, "a@x.af")
    assert client.get("/api/v1/admin/research/summary").status_code == 401
    assert client.get("/api/v1/admin/research/summary", headers=token(client, "b@x.af")).status_code == 403
    assert client.get("/api/v1/admin/research/summary", headers=admin).json()["by_district"][0]["total"] == 2
    r = client.get("/api/v1/admin/research/export.csv", headers=admin)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.strip().splitlines()
    assert lines[0].startswith("order_id,week,district,category,payment_preference") and len(lines) == 3
    assert "b@x.af" not in r.text and "B" not in lines[1].split(",")[0]
