import pytest
from sqlalchemy import select

from app.core.ratelimit import survey_limiter
from app.models import AuditLog, Role, SurveyAnswer, SurveyQuestion, SurveyResponse
from tests.helpers import make_seller, make_user, token


@pytest.fixture(autouse=True)
def _reset_limiter():
    survey_limiter.reset()
    yield
    survey_limiter.reset()


def questions(db, n_per=2):
    out = []
    for i, c in enumerate(["PU", "PEOU", "TR", "CO", "AC", "WA"]):
        for j in range(n_per):
            q = SurveyQuestion(
                construct=c, code=f"{c}{j + 1}", text_en=f"{c} item {j + 1}", position=i * 10 + j, is_reverse_scored=(c == "CO" and j == 1)
            )
            db.add(q)
            out.append(q)
    db.commit()
    return out


def payload(qs, values=None, **kw):
    vals = values or [((i * 7) % 5) + 1 for i in range(len(qs))]
    body = {
        "consent": True,
        "respondent_type": "seller",
        "completion_seconds": 120,
        "answers": [{"question_id": q.id, "value": v} for q, v in zip(qs, vals, strict=True)],
    }
    body.update(kw)
    return body


def test_public_can_read_questionnaire(client, db):
    questions(db)
    r = client.get("/api/v1/survey")
    assert r.status_code == 200 and len(r.json()) == 12 and r.json()[0]["construct"] == "PU"


def test_submit_valid_response_is_anonymous(client, db):
    qs = questions(db)
    r = client.post("/api/v1/survey/responses", json=payload(qs, district="PD4", gender="female", age_band="25-34"))
    assert r.status_code == 201
    row = db.scalar(select(SurveyResponse))
    assert row.is_valid and row.consent and len(row.answers) == 12
    cols = {c.name for c in SurveyResponse.__table__.columns}
    assert not cols & {"ip", "user_id", "email", "phone"}  # nothing identifying is stored
    assert all(
        a.detail == {"valid": True} and a.ip is None and a.actor_id is None
        for a in db.scalars(select(AuditLog).where(AuditLog.action == "survey.submit"))
    )


@pytest.mark.parametrize(
    "mut",
    [
        {"consent": False},
        {"respondent_type": "robot"},
        {"age_band": "99"},
        {"district": "Mars"},
        {"completion_seconds": -1},
    ],
)
def test_invalid_metadata_rejected(client, db, mut):
    qs = questions(db)
    assert client.post("/api/v1/survey/responses", json=payload(qs, **mut)).status_code == 422


def test_all_questions_answered_exactly_once_with_1_to_5(client, db):
    qs = questions(db)
    body = payload(qs)
    assert client.post("/api/v1/survey/responses", json={**body, "answers": body["answers"][:-1]}).status_code == 422  # missing
    assert client.post("/api/v1/survey/responses", json={**body, "answers": body["answers"] + [body["answers"][0]]}).status_code == 422  # duplicate
    bad = payload(qs, values=[6] + [3] * 11)
    assert client.post("/api/v1/survey/responses", json=bad).status_code == 422
    assert client.post("/api/v1/survey/responses", json=payload(qs, values=[0] + [3] * 11)).status_code == 422
    assert db.scalar(select(SurveyResponse)) is None


def test_quality_flags(client, db):
    qs = questions(db)
    client.post("/api/v1/survey/responses", json=payload(qs, completion_seconds=10))
    client.post("/api/v1/survey/responses", json=payload(qs, values=[3] * 12))
    flags = sorted(r.invalid_reason for r in db.scalars(select(SurveyResponse)))
    assert flags == ["straight_lining", "too_fast"]


def test_rate_limit(client, db):
    qs = questions(db)
    codes = [client.post("/api/v1/survey/responses", json=payload(qs)).status_code for _ in range(12)]
    assert codes.count(201) == 10 and codes[-1] == 429


def test_research_endpoints_are_admin_only(client, db):
    make_user(db, "b@x.af", Role.buyer)
    make_seller(db, "s@x.af")
    for path in ("summary", "descriptives", "reliability", "correlations", "regression", "groups", "export.csv"):
        assert client.get(f"/api/v1/admin/research/{path}").status_code == 401
        for who in ("b@x.af", "s@x.af"):
            assert client.get(f"/api/v1/admin/research/{path}", headers=token(client, who)).status_code == 403
    assert client.get("/api/v1/admin/analytics/marketplace", headers=token(client, "b@x.af")).status_code == 403


def test_empty_state_is_graceful(client, db):
    questions(db)
    make_user(db, "a@x.af", Role.admin)
    h = token(client, "a@x.af")
    assert client.get("/api/v1/admin/research/summary", headers=h).json()["valid"] == 0
    assert client.get("/api/v1/admin/research/regression", headers=h).json()["ready"] is False
    assert client.get("/api/v1/admin/research/correlations", headers=h).json()["ready"] is False
    assert client.get("/api/v1/admin/research/descriptives", headers=h).json()["items"] == []
    assert client.get("/api/v1/admin/analytics/marketplace", headers=h).json()["orders"] == 0


def test_export_csv_contains_no_identifiers(client, db):
    qs = questions(db)
    client.post("/api/v1/survey/responses", json=payload(qs))
    make_user(db, "a@x.af", Role.admin)
    r = client.get("/api/v1/admin/research/export.csv", headers=token(client, "a@x.af"))
    head = r.text.splitlines()[0].split(",")
    assert r.headers["content-type"].startswith("text/csv") and "PU1" in head and "WA2" in head
    assert not {"ip", "email", "phone", "user_id"} & set(head) and len(r.text.splitlines()) == 2


def test_reverse_items_recoded_in_analysis(db):
    from app.services import survey as svc

    qs = questions(db, n_per=2)
    r = SurveyResponse(consent=True, respondent_type="seller")
    for q in qs:
        r.answers.append(SurveyAnswer(question_id=q.id, value=1 if q.is_reverse_scored else 5))
    db.add(r)
    db.commit()
    items, scores, _ = svc.load(db)
    assert items.iloc[0]["CO2"] == 5  # 1 reverse-scored -> 5
    assert scores.iloc[0]["CO"] == 5.0
