import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import Conflict, NotFound
from app.core.pagination import PageParams, envelope


def test_production_requires_strong_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="", _env_file=None)
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="short", _env_file=None)
    assert Settings(environment="production", jwt_secret="x" * 40, _env_file=None).jwt_secret


def test_dev_gets_ephemeral_secret_not_hardcoded():
    a, b = Settings(jwt_secret="", _env_file=None), Settings(jwt_secret="", _env_file=None)
    assert a.jwt_secret and a.jwt_secret != b.jwt_secret


def test_cors_list_parsing():
    assert Settings(cors_origins="http://a.com, http://b.com", _env_file=None).cors_list == ["http://a.com", "http://b.com"]


def test_app_errors_carry_status_and_code():
    assert NotFound("x").status_code == 404 and NotFound().code == "not_found"
    assert Conflict().status_code == 409


def test_pagination_envelope():
    p = PageParams(page=3, page_size=10)
    assert p.offset == 20
    e = envelope([1], 25, p)
    assert e["pages"] == 3 and e["total"] == 25
    assert envelope([], 0, PageParams(1, 20))["pages"] == 0
