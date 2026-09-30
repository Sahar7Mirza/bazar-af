import csv
import io

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics import stats as S
from app.core.errors import AppError
from app.models import SurveyAnswer, SurveyQuestion, SurveyResponse
from app.schemas.survey import ResponseIn
from app.services import audit

TARGET = 150
MIN_SECONDS = 30


def active_questions(db: Session) -> list[SurveyQuestion]:
    return list(db.scalars(select(SurveyQuestion).where(SurveyQuestion.is_active).order_by(SurveyQuestion.position)))


def submit(db: Session, data: ResponseIn, ip: str | None = None) -> SurveyResponse:
    qs = {q.id: q for q in active_questions(db)}
    given = [a.question_id for a in data.answers]
    if len(set(given)) != len(given) or set(given) != set(qs):
        raise AppError(
            "Every question must be answered exactly once",
            code="validation_error",
            status_code=422,
            details=[{"field": "answers", "message": "Answer all questions once"}],
        )
    values = [a.value for a in data.answers]
    reason = None
    if data.completion_seconds is not None and data.completion_seconds < MIN_SECONDS:
        reason = "too_fast"
    elif len(set(values)) == 1:
        reason = "straight_lining"
    r = SurveyResponse(
        consent=True,
        respondent_type=data.respondent_type,
        age_band=data.age_band,
        gender=data.gender,
        district=data.district,
        business_type=data.business_type,
        uses_mobile_money=data.uses_mobile_money,
        completion_seconds=data.completion_seconds,
        is_valid=reason is None,
        invalid_reason=reason,
    )
    r.answers = [SurveyAnswer(question_id=a.question_id, value=a.value) for a in data.answers]
    db.add(r)
    db.flush()
    audit.record(db, "survey.submit", entity_type="survey_response", entity_id=r.id, detail={"valid": r.is_valid})  # no IP: anonymity
    db.commit()
    return r


# ---------- analysis
def _filters(stmt, respondent_type=None, district=None, valid_only=True):
    if valid_only:
        stmt = stmt.where(SurveyResponse.is_valid)
    if respondent_type:
        stmt = stmt.where(SurveyResponse.respondent_type == respondent_type)
    if district:
        stmt = stmt.where(SurveyResponse.district == district)
    return stmt


def load(db: Session, respondent_type=None, district=None):
    qs = active_questions(db)
    item_construct = {q.code: q.construct for q in qs}
    stmt = _filters(
        select(SurveyAnswer.response_id, SurveyQuestion.construct, SurveyQuestion.code, SurveyAnswer.value, SurveyQuestion.is_reverse_scored)
        .join(SurveyQuestion, SurveyQuestion.id == SurveyAnswer.question_id)
        .join(SurveyResponse, SurveyResponse.id == SurveyAnswer.response_id),
        respondent_type,
        district,
    )
    rows = [tuple(r) for r in db.execute(stmt)]
    items = S.item_frame(rows)
    scores = S.construct_scores(items, item_construct) if not items.empty else pd.DataFrame()
    return items, scores, item_construct


def summary(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(SurveyResponse)) or 0
    valid = db.scalar(select(func.count()).select_from(SurveyResponse).where(SurveyResponse.is_valid)) or 0
    reasons = dict(
        db.execute(select(SurveyResponse.invalid_reason, func.count()).where(~SurveyResponse.is_valid).group_by(SurveyResponse.invalid_reason)).all()
    )
    by_type = dict(
        db.execute(select(SurveyResponse.respondent_type, func.count()).where(SurveyResponse.is_valid).group_by(SurveyResponse.respondent_type)).all()
    )
    synthetic = db.scalar(select(func.count()).select_from(SurveyResponse).where(SurveyResponse.is_synthetic)) or 0
    return {
        "total": total,
        "valid": valid,
        "invalid": total - valid,
        "invalid_reasons": reasons,
        "target": TARGET,
        "progress_pct": min(100, round(valid / TARGET * 100)),
        "by_respondent_type": by_type,
        "synthetic": synthetic,
        "uses_mobile_money": _share(db),
    }


def _share(db: Session):
    rows = dict(
        db.execute(
            select(SurveyResponse.uses_mobile_money, func.count())
            .where(SurveyResponse.is_valid, SurveyResponse.uses_mobile_money.is_not(None))
            .group_by(SurveyResponse.uses_mobile_money)
        ).all()
    )
    return {"yes": rows.get(True, 0), "no": rows.get(False, 0)}


def group_table(db: Session, by: str, respondent_type=None, district=None):
    col = {
        "uses_mobile_money": SurveyResponse.uses_mobile_money,
        "respondent_type": SurveyResponse.respondent_type,
        "gender": SurveyResponse.gender,
        "age_band": SurveyResponse.age_band,
        "district": SurveyResponse.district,
    }[by]
    _, scores, _ = load(db, respondent_type, district)
    if scores.empty or "WA" not in scores:
        return None
    meta = pd.DataFrame(
        db.execute(_filters(select(SurveyResponse.id, col.label("g")), respondent_type, district)).all(), columns=["rid", "g"]
    ).set_index("rid")
    return S.group_difference(scores, meta["g"].reindex(scores.index).astype("object"))


def export_csv(db: Session) -> str:
    qs = active_questions(db)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "response_id",
            "respondent_type",
            "age_band",
            "gender",
            "district",
            "business_type",
            "uses_mobile_money",
            "completion_seconds",
            "is_valid",
            "is_synthetic",
        ]
        + [q.code for q in qs]
    )
    for r in db.scalars(select(SurveyResponse).order_by(SurveyResponse.id)):
        ans = {a.question_id: a.value for a in r.answers}
        w.writerow(
            [
                r.id,
                r.respondent_type,
                r.age_band or "",
                r.gender or "",
                r.district or "",
                r.business_type or "",
                "" if r.uses_mobile_money is None else int(r.uses_mobile_money),
                r.completion_seconds or "",
                int(r.is_valid),
                int(r.is_synthetic),
            ]
            + [ans.get(q.id, "") for q in qs]
        )
    return buf.getvalue()
