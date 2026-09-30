import time

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, hash_password, hash_token, new_refresh_token, verify_password
from app.schemas.auth import RegisterIn


def test_password_hash_roundtrip_and_salting():
    h1, h2 = hash_password("Sup3rSecret!!"), hash_password("Sup3rSecret!!")
    assert h1 != h2 and h1.startswith("$2b$12$")
    assert verify_password("Sup3rSecret!!", h1) and not verify_password("wrong", h1)
    assert not verify_password("x", "not-a-hash")


def test_access_token_contents_and_expiry():
    tok, ttl = create_access_token(7, "seller")
    d = decode_access_token(tok)
    assert d["sub"] == "7" and d["role"] == "seller" and ttl == 900
    expired = jwt.encode({"sub": "1", "exp": int(time.time()) - 5, "typ": "access"}, get_settings().jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(expired)


def test_token_signed_with_other_key_or_alg_none_rejected():
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 60, "typ": "access"}, "x" * 40, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(forged)
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(jwt.encode({"sub": "1", "exp": int(time.time()) + 60, "typ": "access"}, None, algorithm="none"))


def test_refresh_token_is_random_and_stored_hashed():
    a, ha = new_refresh_token()
    b, _ = new_refresh_token()
    assert a != b and ha == hash_token(a) and a not in ha


@pytest.mark.parametrize("pw", ["short1", "onlyletterslong", "1234567890123"])
def test_weak_passwords_rejected(pw):
    with pytest.raises(ValueError):
        RegisterIn(email="a@b.af", password=pw, full_name="Ab")


def test_admin_role_cannot_be_self_registered():
    with pytest.raises(ValueError):
        RegisterIn(email="a@b.af", password="Str0ngPassw0rd", full_name="Ab", role="admin")


def test_phone_normalised_and_validated():
    ok = RegisterIn(email="a@b.af", password="Str0ngPassw0rd", full_name="Ab", phone="+93 70-000 0001")
    assert ok.phone == "+93700000001"
    with pytest.raises(ValueError):
        RegisterIn(email="a@b.af", password="Str0ngPassw0rd", full_name="Ab", phone="abc")
