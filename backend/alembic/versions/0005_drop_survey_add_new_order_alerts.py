"""drop the survey tables (adoption is now measured from checkout choices)

Revision ID: 0005
Revises: 0004
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("survey_answers")
    op.drop_table("survey_responses")
    op.drop_table("survey_questions")
    # Seller "new order" alerts are looked up by user and kind; keep that fast while polling every few seconds.
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "read_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.create_table(
        "survey_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("construct", sa.String(5), nullable=False),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("text_en", sa.Text(), nullable=False),
        sa.Column("text_fa", sa.Text()),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_reverse_scored", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("construct IN ('PU','PEOU','TR','CO','AC','WA')", name="ck_construct"),
    )
    op.create_table(
        "survey_responses",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("consent", sa.Boolean(), nullable=False),
        sa.Column("respondent_type", sa.String(10), nullable=False),
        sa.Column("age_band", sa.String(10)),
        sa.Column("gender", sa.String(20)),
        sa.Column("district", sa.String(40)),
        sa.Column("business_type", sa.String(60)),
        sa.Column("uses_mobile_money", sa.Boolean()),
        sa.Column("completion_seconds", sa.Integer()),
        sa.Column("is_valid", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("invalid_reason", sa.String(60)),
        sa.Column("is_synthetic", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("consent", name="ck_consent"),
        sa.CheckConstraint("respondent_type IN ('seller','buyer','other')", name="ck_resp_type"),
    )
    op.create_table(
        "survey_answers",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("response_id", sa.BigInteger(), sa.ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("survey_questions.id"), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.UniqueConstraint("response_id", "question_id"),
        sa.CheckConstraint("value BETWEEN 1 AND 5", name="ck_likert"),
    )
    op.create_index(op.f("ix_survey_answers_question_id"), "survey_answers", ["question_id"], unique=False)
