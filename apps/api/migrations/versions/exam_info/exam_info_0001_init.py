"""exam_info: exam profiles, sections, certificate rules, events, FAQ

Revision ID: exam_info_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "exam_info_0001"
down_revision = None
branch_labels = ("exam_info",)
depends_on = None

S = "exam_info"


def _uuid() -> postgresql.UUID:
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    f = sa.text("false")
    t = sa.text("true")

    op.create_table(
        "exam_profile",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("direction_code", sa.String(16)),
        sa.Column("group_code", sa.String(32)),
        sa.Column("names", postgresql.JSONB, nullable=False),
        sa.Column("exam_year", sa.Integer, nullable=False),
        sa.Column("exam_date", sa.Date),
        sa.Column("date_verified", sa.Boolean, nullable=False, server_default=f),
        sa.Column("max_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("trust_self_declared", sa.Boolean, nullable=False, server_default=f),
        sa.Column("taper_days", sa.Integer, nullable=False, server_default=sa.text("6")),
        sa.Column("mock_blueprint_id", _uuid()),
        sa.Column("source_url", sa.Text),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=f),
        sa.Column("active", sa.Boolean, nullable=False, server_default=t),
        sa.Column("position", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("code", name="uq_exam_profile_code"),
        sa.UniqueConstraint("direction_code", "exam_year", name="uq_exam_profile_direction_year"),
        sa.CheckConstraint("taper_days between 5 and 7", name="ck_exam_profile_taper"),
        schema=S,
    )
    op.create_table(
        "exam_profile_section",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column(
            "profile_id",
            _uuid(),
            sa.ForeignKey(
                f"{S}.exam_profile.id", ondelete="CASCADE", name="fk_exam_section_profile"
            ),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("slot", sa.Integer, nullable=False),
        sa.Column("subject_id", _uuid()),
        sa.Column("subject_code", sa.String(64)),
        sa.Column("names", postgresql.JSONB, nullable=False),
        sa.Column("choice_group", sa.String(32)),
        sa.Column("question_count", sa.Integer),
        sa.Column("points_per_question", sa.Numeric(4, 2)),
        sa.Column("max_points", sa.Numeric(6, 2), nullable=False),
        sa.Column("exemptible", sa.Boolean, nullable=False, server_default=t),
        sa.Column("position", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("profile_id", "slot", name="uq_exam_section_slot"),
        sa.CheckConstraint("(role = 'iq') = (slot = 0)", name="ck_exam_section_iq_slot"),
        sa.CheckConstraint(
            "role <> 'iq' or not exemptible", name="ck_exam_section_iq_not_exemptible"
        ),
        sa.CheckConstraint("role in ('iq', 'subject', 'creative')", name="ck_exam_section_role"),
        schema=S,
    )
    op.create_table(
        "exam_subject_choice",
        sa.Column("choice_group", sa.String(32), primary_key=True),
        sa.Column("subject_id", _uuid(), primary_key=True),
        sa.Column("position", sa.Integer, nullable=False, server_default=sa.text("0")),
        schema=S,
    )
    op.create_table(
        "exam_certificate_rule",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column(
            "section_id",
            _uuid(),
            sa.ForeignKey(
                f"{S}.exam_profile_section.id", ondelete="CASCADE", name="fk_exam_cert_rule_section"
            ),
            nullable=False,
        ),
        sa.Column("cert_type", sa.String(16), nullable=False),
        sa.Column("language_subject_id", _uuid()),
        sa.Column("level_label", sa.String(64)),
        sa.Column("min_value", sa.Numeric(6, 1)),
        sa.Column(
            "awarded_fraction", sa.Numeric(3, 2), nullable=False, server_default=sa.text("1.0")
        ),
        sa.Column("note", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=f),
        sa.Column("source_url", sa.Text),
        sa.Column("active", sa.Boolean, nullable=False, server_default=t),
        sa.UniqueConstraint(
            "section_id",
            "cert_type",
            "language_subject_id",
            "min_value",
            name="uq_exam_cert_rule_key",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint("awarded_fraction between 0 and 1", name="ck_exam_cert_rule_fraction"),
        sa.CheckConstraint(
            "not active or min_value is not null", name="ck_exam_cert_rule_active_min"
        ),
        sa.CheckConstraint(
            "cert_type in ('cefr', 'ielts', 'toefl', 'national', 'other_intl')",
            name="ck_exam_cert_rule_type",
        ),
        schema=S,
    )
    op.create_table(
        "exam_event",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("exam_year", sa.Integer, nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date),
        sa.Column("label", postgresql.JSONB, nullable=False),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=f),
        sa.Column("source_url", sa.Text),
        sa.Column("position", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("exam_year", "kind", name="uq_exam_event_year_kind"),
        sa.CheckConstraint("ends_on is null or ends_on >= starts_on", name="ck_exam_event_range"),
        sa.CheckConstraint(
            "kind in ('applications', 'test', 'results', 'appeal')", name="ck_exam_event_kind"
        ),
        schema=S,
    )
    op.create_table(
        "faq_item",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("question", postgresql.JSONB, nullable=False),
        sa.Column("answer", postgresql.JSONB, nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("published", sa.Boolean, nullable=False, server_default=t),
        sa.Column("source_url", sa.Text),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=f),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_by", _uuid()),
        sa.UniqueConstraint("key", name="uq_faq_item_key"),
        schema=S,
    )


def downgrade() -> None:
    for table in (
        "faq_item",
        "exam_event",
        "exam_certificate_rule",
        "exam_subject_choice",
        "exam_profile_section",
        "exam_profile",
    ):
        op.drop_table(table, schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
