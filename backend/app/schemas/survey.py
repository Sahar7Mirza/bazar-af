from pydantic import BaseModel, Field, field_validator

from app.schemas.catalog import DISTRICTS


class AnswerIn(BaseModel):
    question_id: int
    value: int = Field(ge=1, le=5)


class ResponseIn(BaseModel):
    consent: bool
    respondent_type: str = Field(pattern="^(seller|buyer|other)$")
    age_band: str | None = Field(default=None, pattern=r"^(18-24|25-34|35-44|45-54|55\+)$")
    gender: str | None = Field(default=None, pattern="^(female|male|prefer_not_to_say)$")
    district: str | None = None
    business_type: str | None = Field(default=None, max_length=60)
    uses_mobile_money: bool | None = None
    completion_seconds: int | None = Field(default=None, ge=0, le=86400)
    answers: list[AnswerIn] = Field(min_length=1, max_length=100)

    @field_validator("consent")
    @classmethod
    def must_consent(cls, v):
        if not v:
            raise ValueError("Consent is required to take part")
        return v

    @field_validator("district")
    @classmethod
    def known_district(cls, v):
        if v is not None and v not in DISTRICTS:
            raise ValueError("Unknown district")
        return v
