def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_ready_checks_database(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200 and r.json()["database"] == "up"


def test_request_id_generated_and_echoed(client):
    assert client.get("/api/v1/health").headers["x-request-id"]
    assert client.get("/api/v1/health", headers={"X-Request-ID": "abc123"}).headers["x-request-id"] == "abc123"


def test_security_headers(client):
    h = client.get("/api/v1/health").headers
    assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"


def test_unknown_route_uses_error_format(client):
    r = client.get("/api/v1/nope", headers={"X-Request-ID": "rid1"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found" and r.json()["error"]["request_id"] == "rid1"


def test_unhandled_error_hides_internals(client):
    from app.main import app

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret detail")

    r = client.get("/boom")
    assert r.status_code == 500 and "secret" not in r.text and r.json()["error"]["code"] == "internal_error"
