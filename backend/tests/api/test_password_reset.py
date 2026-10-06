from datetime import UTC, datetime, timedelta

import pytest

from app.models import EmailToken, RefreshToken, User
from tests.helpers import PW, make_user, token


@pytest.fixture()
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr("app.services.auth.mail.send_email", lambda to, subject, text, link=None: sent.append((to, subject, link)) or True)
    return sent


def _tok(link):
    return link.split("token=")[1]


def test_register_sends_verification_and_link_verifies(client, db, outbox):
    r = client.post("/api/v1/auth/register", json={"email": "new@x.af", "password": PW, "full_name": "New Person"})
    assert r.status_code == 201 and r.json()["email_verified_at"] is None
    to, subject, link = outbox[0]
    assert to == "new@x.af" and "/verify-email?token=" in link
    assert client.post("/api/v1/auth/verify-email", json={"token": _tok(link)}).status_code == 200
    h = token(client, "new@x.af")
    assert client.get("/api/v1/auth/me", headers=h).json()["email_verified_at"] is not None
    assert client.post("/api/v1/auth/verify-email", json={"token": _tok(link)}).status_code == 400  # one use only


def test_forgot_password_is_identical_for_known_and_unknown_emails(client, db, outbox):
    make_user(db, "a@x.af")
    known = client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@x.af"})
    assert known.status_code == unknown.status_code == 202 and known.json() == unknown.json()
    assert len(outbox) == 1 and outbox[0][0] == "a@x.af"


def test_reset_changes_password_signs_out_everywhere_and_works_once(client, db, outbox):
    make_user(db, "a@x.af")
    token(client, "a@x.af")  # creates a refresh token
    client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"})
    t = _tok(outbox[0][2])
    new = "BrandNewPass99"
    assert client.post("/api/v1/auth/reset-password", json={"token": t, "password": new}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "a@x.af", "password": PW}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"email": "a@x.af", "password": new}).status_code == 200
    assert db.query(RefreshToken).filter(RefreshToken.revoked_at.is_(None)).count() == 1  # only the fresh login
    again = client.post("/api/v1/auth/reset-password", json={"token": t, "password": "AnotherPass123"})
    assert again.status_code == 400 and again.json()["error"]["code"] == "invalid_token"


def test_reset_rejects_weak_password_expired_and_made_up_tokens(client, db, outbox):
    make_user(db, "a@x.af")
    client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"})
    t = _tok(outbox[0][2])
    assert client.post("/api/v1/auth/reset-password", json={"token": t, "password": "short"}).status_code == 422
    assert client.post("/api/v1/auth/reset-password", json={"token": "x" * 40, "password": "BrandNewPass99"}).status_code == 400
    db.query(EmailToken).update({"expires_at": datetime.now(UTC) - timedelta(minutes=1)})
    db.commit()
    assert client.post("/api/v1/auth/reset-password", json={"token": t, "password": "BrandNewPass99"}).status_code == 400


def test_reset_clears_a_lockout_and_a_new_request_replaces_the_old_link(client, db, outbox):
    u = make_user(db, "a@x.af")
    client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"})
    first = _tok(outbox[0][2])
    db.query(EmailToken).update({"created_at": datetime.now(UTC) - timedelta(minutes=5)})  # get past the one-minute cooldown
    u.locked_until = datetime.now(UTC) + timedelta(minutes=10)
    db.commit()
    client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"})
    second = _tok(outbox[1][2])
    assert client.post("/api/v1/auth/reset-password", json={"token": first, "password": "BrandNewPass99"}).status_code == 400  # old link is dead
    assert client.post("/api/v1/auth/reset-password", json={"token": second, "password": "BrandNewPass99"}).status_code == 200
    db.expire_all()
    assert db.get(User, u.id).locked_until is None


def test_emails_have_a_one_minute_cooldown(client, db, outbox):
    make_user(db, "a@x.af")
    for _ in range(3):
        assert client.post("/api/v1/auth/forgot-password", json={"email": "a@x.af"}).status_code == 202
    assert len(outbox) == 1


def test_resend_verification_needs_login_and_skips_verified(client, db, outbox):
    u = make_user(db, "a@x.af")
    assert client.post("/api/v1/auth/resend-verification").status_code == 401
    h = token(client, "a@x.af")
    assert client.post("/api/v1/auth/resend-verification", headers=h).status_code == 202 and len(outbox) == 1
    u.email_verified_at = datetime.now(UTC)
    db.commit()
    assert client.post("/api/v1/auth/resend-verification", headers=h).status_code == 202 and len(outbox) == 1


def test_mail_without_api_key_never_raises_and_resend_payload_is_correct(monkeypatch):
    from app.core import config, mail

    config.get_settings.cache_clear()
    monkeypatch.setenv("RESEND_API_KEY", "")
    assert mail.send_email("a@x.af", "Hi", "Hello", "http://x/y") is False
    config.get_settings.cache_clear()
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    seen = {}

    class Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_open(req, timeout):
        seen["url"], seen["auth"], seen["body"] = req.full_url, req.headers["Authorization"], req.data.decode()
        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    assert mail.send_email("a@x.af", "Subject", "Hello there", "http://x/y") is True
    assert seen["url"] == "https://api.resend.com/emails" and seen["auth"] == "Bearer re_test_key" and '"to": ["a@x.af"]' in seen["body"]
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))
    assert mail.send_email("a@x.af", "Subject", "Hello", None) is False  # a mail outage must not break the request
    config.get_settings.cache_clear()
