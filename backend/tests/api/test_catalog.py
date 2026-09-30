from app.models import Role, SellerStatus
from tests.helpers import make_category, make_product, make_seller, make_user, token


def test_public_listing_hides_pending_hidden_and_deleted(client, db):
    _, ok = make_seller(db, "ok@x.af")
    _, pending = make_seller(db, "p@x.af", SellerStatus.pending)
    make_product(db, ok, "Visible")
    make_product(db, ok, "Hidden", status="hidden")
    make_product(db, ok, "AdminHidden", hidden_by_admin=True)
    make_product(db, pending, "PendingShop")
    names = [i["name"] for i in client.get("/api/v1/products").json()["items"]]
    assert names == ["Visible"]


def test_search_filter_sort_pagination(client, db):
    _, sp = make_seller(db, "s@x.af")
    cat = make_category(db)
    for i in range(25):
        make_product(db, sp, f"Naan {i:02d}", price=str(10 + i), category_id=cat.id)
    make_product(db, sp, "Rice", price="500")
    r = client.get("/api/v1/products", params={"q": "naan", "page_size": 10, "sort": "price", "order": "asc"}).json()
    assert r["total"] == 25 and r["pages"] == 3 and len(r["items"]) == 10 and r["items"][0]["name"] == "Naan 00"
    r = client.get("/api/v1/products", params={"min_price": 500}).json()
    assert [i["name"] for i in r["items"]] == ["Rice"]
    assert client.get("/api/v1/products", params={"district": "PD4"}).json()["total"] == 26
    assert client.get("/api/v1/products", params={"district": "PD9"}).json()["total"] == 0
    assert client.get("/api/v1/products", params={"page": 3, "page_size": 10, "q": "naan"}).json()["items"][0]["name"]


def test_search_treats_wildcards_literally(client, db):
    _, sp = make_seller(db, "s@x.af")
    make_product(db, sp, "100% Wool")
    make_product(db, sp, "Other")
    assert client.get("/api/v1/products", params={"q": "%"}).json()["total"] == 1
    assert client.get("/api/v1/products", params={"q": "_"}).json()["total"] == 0


def test_pagination_limits_validated(client):
    assert client.get("/api/v1/products", params={"page_size": 1000}).status_code == 422
    assert client.get("/api/v1/products", params={"page": 0}).status_code == 422
    assert client.get("/api/v1/products", params={"sort": "password"}).status_code == 422


def test_seller_product_crud_and_validation(client, db):
    make_seller(db, "s@x.af")
    h = token(client, "s@x.af")
    bad = client.post("/api/v1/products", json={"name": "X", "price_afn": -5}, headers=h)
    assert bad.status_code == 422
    r = client.post("/api/v1/products", json={"name": "Tea", "price_afn": "12.50", "stock_qty": 5, "unit": "box"}, headers=h)
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.patch(f"/api/v1/products/{pid}", json={"price_afn": "15.00"}, headers=h).json()["price_afn"] == "15.00"
    assert client.delete(f"/api/v1/products/{pid}", headers=h).status_code == 204
    assert client.get(f"/api/v1/products/{pid}").status_code == 404
    assert client.get("/api/v1/sellers/me/products", headers=h).json()["total"] == 0


def test_unapproved_seller_cannot_create_products(client, db):
    make_seller(db, "s@x.af", SellerStatus.pending)
    r = client.post("/api/v1/products", json={"name": "Tea", "price_afn": 1}, headers=token(client, "s@x.af"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "seller_not_approved"


def test_seller_cannot_touch_another_sellers_product(client, db):
    _, a = make_seller(db, "a@x.af", name="A")
    make_seller(db, "b@x.af", name="B")
    p = make_product(db, a)
    hb = token(client, "b@x.af")
    assert client.patch(f"/api/v1/products/{p.id}", json={"name": "Hacked"}, headers=hb).status_code == 404
    assert client.delete(f"/api/v1/products/{p.id}", headers=hb).status_code == 404


def test_buyer_and_anonymous_cannot_manage_products(client, db):
    make_user(db, "b@x.af", Role.buyer)
    body = {"name": "Tea", "price_afn": 1}
    assert client.post("/api/v1/products", json=body).status_code == 401
    assert client.post("/api/v1/products", json=body, headers=token(client, "b@x.af")).status_code == 403


def test_seller_cannot_unhide_admin_hidden_product(client, db):
    _, sp = make_seller(db, "s@x.af")
    p = make_product(db, sp, hidden_by_admin=True, status="hidden")
    r = client.patch(f"/api/v1/products/{p.id}", json={"status": "active"}, headers=token(client, "s@x.af"))
    assert r.status_code == 403


def test_seller_profile_update_and_public_view(client, db):
    _, sp = make_seller(db, "s@x.af")
    h = token(client, "s@x.af")
    r = client.put("/api/v1/sellers/me", json={"business_name": "New Name", "district": "PD10", "opening_hours": "8-18"}, headers=h)
    assert r.status_code == 200 and r.json()["business_name"] == "New Name"
    assert client.put("/api/v1/sellers/me", json={"business_name": "N", "district": "Mars"}, headers=h).status_code == 422
    pub = client.get(f"/api/v1/sellers/{sp.id}")
    assert pub.status_code == 200 and pub.json()["review_note"] is None


def test_pending_seller_not_public(client, db):
    _, sp = make_seller(db, "s@x.af", SellerStatus.pending)
    assert client.get(f"/api/v1/sellers/{sp.id}").status_code == 404


def test_categories_public(client, db):
    make_category(db, "Bakery")
    assert [c["name"] for c in client.get("/api/v1/categories").json()] == ["Bakery"]
