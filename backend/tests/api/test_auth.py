from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.deps import require_roles
from app.models import AuditLog, RefreshToken, Role, User

PW = "Str0ngPassw0rd"


def reg(client, email="buyer@x.af", role="buyer", **kw):
    body = {"email": email, "password": PW, "full_name": "Test User", "role": role, **kw}
    return client.post("/api/v1/auth/register", json=body)


def login(client, email="buyer@x.af", password=PW):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth(tok):
    return {"Authorization": f"Bearer {tok}"}


def test_register_buyer_and_no_secrets_in_response(client):
    r = reg(client)
    assert r.status_code == 201
    assert r.json()["role"] == "buyer" and "password" not in r.text and "hash" not in r.text


def test_register_seller_creates_pending_profile(client, db):
    assert reg(client, "s@x.af", "seller", business_name="Kabul Bakery").status_code == 201
    u = db.scalar(select(User).where(User.email == "s@x.af"))
    assert u.seller_profile.status.value == "pending" and u.seller_profile.business_name == "Kabul Bakery"


def test_seller_requires_business_name(client):
    r = reg(client, "s@x.af", "seller")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_cannot_register_admin(client):
    assert reg(client, "a@x.af", "admin").status_code == 422


def test_duplicate_email_case_insensitive(client):
    reg(client)
    r = reg(client, "BUYER@x.af")
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_taken"


def test_validation_details_are_field_level(client):
    r = client.post("/api/v1/auth/register", json={"email": "bad", "password": "x", "full_name": "A"})
    fields = {d["field"] for d in r.json()["error"]["details"]}
    assert r.status_code == 422 and {"email", "password", "full_name"} <= fields


def test_login_me_roundtrip(client):
    reg(client)
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    me = client.get("/api/v1/auth/me", headers=auth(body["access_token"]))
    assert me.status_code == 200 and me.json()["email"] == "buyer@x.af"


def test_login_errors_do_not_reveal_which_part_was_wrong(client):
    reg(client)
    a = login(client, password="Wrong-Passw0rd")
    b = login(client, email="nobody@x.af")
    assert a.status_code == b.status_code == 401
    assert a.json()["error"]["message"] == b.json()["error"]["message"]


def test_me_requires_valid_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers=auth("garbage")).status_code == 401


def test_lockout_after_five_failures_then_correct_password_blocked(client):
    reg(client)
    for _ in range(5):
        assert login(client, password="Wrong-Passw0rd").status_code == 401
    r = login(client)
    assert r.status_code == 429 and r.json()["error"]["code"] == "account_locked"


def test_lockout_expires(client, db):
    reg(client)
    for _ in range(5):
        login(client, password="Wrong-Passw0rd")
    u = db.scalar(select(User).where(User.email == "buyer@x.af"))
    u.locked_until = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert login(client).status_code == 200


def test_deactivated_user_cannot_login_or_use_token(client, db):
    reg(client)
    tok = login(client).json()["access_token"]
    u = db.scalar(select(User).where(User.email == "buyer@x.af"))
    u.is_active = False
    db.commit()
    assert client.get("/api/v1/auth/me", headers=auth(tok)).status_code == 401
    assert login(client).status_code == 403


def test_refresh_rotates_and_old_token_is_dead(client):
    reg(client)
    t1 = login(client).json()
    t2 = client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert t2.status_code == 200 and t2.json()["refresh_token"] != t1["refresh_token"]
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})
    assert again.status_code == 401


def test_refresh_reuse_revokes_whole_family(client, db):
    reg(client)
    t1 = login(client).json()
    t2 = client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    client.post("/api/v1/auth/refresh", json={"refresh_token": t1["refresh_token"]})  # replay of stolen token
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t2["refresh_token"]}).status_code == 401
    assert all(t.revoked_at for t in db.scalars(select(RefreshToken)))
    assert db.scalar(select(AuditLog).where(AuditLog.action == "auth.refresh_reuse"))


def test_logout_revokes_refresh_token(client):
    reg(client)
    t = login(client).json()
    assert client.post("/api/v1/auth/logout", json={"refresh_token": t["refresh_token"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_refresh_tokens_stored_only_as_hashes(client, db):
    reg(client)
    t = login(client).json()
    assert all(t["refresh_token"] != r.token_hash and len(r.token_hash) == 64 for r in db.scalars(select(RefreshToken)))


def test_audit_trail_has_no_secrets_and_has_timestamps(client, db):
    reg(client)
    login(client, password="Wrong-Passw0rd")
    login(client)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert [r.action for r in rows] == ["user.register", "auth.login_failed", "auth.login"]
    assert all(r.created_at and PW not in str(r.detail) for r in rows)


@pytest.fixture()
def rbac_app(client):
    from app.main import app

    @app.get("/t/admin", dependencies=[__import__("fastapi").Depends(require_roles(Role.admin))])
    def only_admin():
        return {"ok": True}

    @app.get("/t/sellers", dependencies=[__import__("fastapi").Depends(require_roles(Role.seller, Role.admin))])
    def sellers():
        return {"ok": True}

    return client


def test_rbac_blocks_wrong_role_and_anonymous(rbac_app):
    c = rbac_app
    assert c.get("/t/admin").status_code == 401
    reg(c)
    tok = login(c).json()["access_token"]
    r = c.get("/t/admin", headers=auth(tok))
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
    assert c.get("/t/sellers", headers=auth(tok)).status_code == 403


def test_rbac_allows_right_role(rbac_app, db):
    c = rbac_app
    reg(c, "s@x.af", "seller", business_name="Shop")
    tok = login(c, "s@x.af").json()["access_token"]
    assert c.get("/t/sellers", headers=auth(tok)).status_code == 200
    assert c.get("/t/admin", headers=auth(tok)).status_code == 403
