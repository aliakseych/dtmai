"""lyceums: seed AL IHT specialization and offerings (only facts confirmed by the product owner)

Revision ID: lyceums_0008
Revises: lyceums_0007
Create Date: 2026-11-12
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "lyceums_0008"
down_revision = "lyceums_0007"
branch_labels = None
depends_on = None

SPECIALIZATIONS = [
    {
        "field_code": "Aniq fanlar-3",
        "name": {
            "uz-Latn": "Texnik-dasturchi",
            "uz-Cyrl": "Техник-дастурчи",
            "ru": "Технический программист",
            "en": "Technical programmer",
        },
        "description": {},
        "second_year_subjects": [{"uz-Latn": "C++", "uz-Cyrl": "C++", "ru": "C++", "en": "C++"}],
    }
]
OFFERINGS = [
    {
        "title": {
            "uz-Latn": "SAT tayyorgarligi",
            "uz-Cyrl": "SAT тайёргарлиги",
            "ru": "Подготовка к SAT",
            "en": "SAT preparation",
        },
        "description": {},
        "taught_by": {},
    },
    {
        "title": {
            "uz-Latn": "Avtomatlashtirish asoslari",
            "uz-Cyrl": "Автоматлаштириш асослари",
            "ru": "Основы автоматизации",
            "en": "Fundamentals of automation",
        },
        "description": {},
        "taught_by": {
            "uz-Latn": "Universitet talabalari",
            "uz-Cyrl": "Университет талабалари",
            "ru": "Студенты университета",
            "en": "University students",
        },
    },
]


def upgrade() -> None:
    # Matches by name; a no-op where the lyceum has not been imported yet or already has data.
    op.get_bind().execute(
        sa.text(
            "UPDATE lyceums.lyceums SET specializations = CAST(:s AS json), "
            "offerings = CAST(:o AS json) "
            "WHERE (name_uz ILIKE '%AL IHT%' OR name_uz ILIKE '%Al-Xorazmiy%IHT%') "
            "AND specializations::text = '[]' AND offerings::text = '[]'"
        ),
        {"s": json.dumps(SPECIALIZATIONS), "o": json.dumps(OFFERINGS)},
    )


def downgrade() -> None:
    pass
