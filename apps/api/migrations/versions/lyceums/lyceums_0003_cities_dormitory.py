"""lyceums: cities table, city codes on lyceums, dormitory fields

Revision ID: lyceums_0003
Revises: lyceums_0002
Create Date: 2026-11-15
"""

import re

import sqlalchemy as sa
from alembic import op

revision = "lyceums_0003"
down_revision = "lyceums_0002"
branch_labels = None
depends_on = None

S = "lyceums"

# code, uz-Latn, uz-Cyrl, ru, en
CITIES = [
    ("tashkent", "Toshkent", "Тошкент", "Ташкент", "Tashkent"),
    ("nurafshon", "Nurafshon", "Нурафшон", "Нурафшон", "Nurafshon"),
    ("nukus", "Nukus", "Нукус", "Нукус", "Nukus"),
    ("andijan", "Andijon", "Андижон", "Андижан", "Andijan"),
    ("bukhara", "Buxoro", "Бухоро", "Бухара", "Bukhara"),
    ("jizzakh", "Jizzax", "Жиззах", "Джизак", "Jizzakh"),
    ("karshi", "Qarshi", "Қарши", "Карши", "Karshi"),
    ("navoi", "Navoiy", "Навоий", "Навои", "Navoi"),
    ("namangan", "Namangan", "Наманган", "Наманган", "Namangan"),
    ("samarkand", "Samarqand", "Самарқанд", "Самарканд", "Samarkand"),
    ("gulistan", "Guliston", "Гулистон", "Гулистан", "Gulistan"),
    ("termez", "Termiz", "Термиз", "Термез", "Termez"),
    ("fergana", "Farg‘ona", "Фарғона", "Фергана", "Fergana"),
    ("urgench", "Urganch", "Урганч", "Ургенч", "Urgench"),
    ("chirchiq", "Chirchiq", "Чирчиқ", "Чирчик", "Chirchiq"),
    ("kokand", "Qo‘qon", "Қўқон", "Коканд", "Kokand"),
    ("angren", "Angren", "Ангрен", "Ангрен", "Angren"),
    ("almalyk", "Olmaliq", "Олмалиқ", "Алмалык", "Almalyk"),
    ("bekabad", "Bekobod", "Бекобод", "Бекабад", "Bekabad"),
    ("margilan", "Marg‘ilon", "Марғилон", "Маргилан", "Margilan"),
    ("shahrisabz", "Shahrisabz", "Шаҳрисабз", "Шахрисабз", "Shahrisabz"),
    ("zarafshan", "Zarafshon", "Зарафшон", "Зарафшан", "Zarafshan"),
    ("kattakurgan", "Kattaqo‘rg‘on", "Каттақўрғон", "Каттакурган", "Kattakurgan"),
    ("khiva", "Xiva", "Хива", "Хива", "Khiva"),
]

_REGION_WORDS = ("viloyat", "область", "вилоят", "region", "oblast")
_APOS = str.maketrans({"ʻ": "'", "‘": "'", "’": "'", "ʼ": "'", "`": "'", "´": "'"})


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_APOS).lower())


def _match(names: list[str], variants: dict[str, list[str]]) -> str | None:
    """The single city code mentioned by the lyceum names, else None (ambiguous or none)."""
    haystack = [_norm(n) for n in names if n]
    if any(w in h for h in haystack for w in _REGION_WORDS):
        return None
    found = {
        code for code, vs in variants.items()
        if any(re.search(rf"(?<!\w){re.escape(v)}(?!\w)", h) for v in vs for h in haystack)
    }
    return found.pop() if len(found) == 1 else None


def upgrade() -> None:
    cities = op.create_table(
        "cities",
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name_uz_latn", sa.Text(), nullable=False),
        sa.Column("name_uz_cyrl", sa.Text(), nullable=False),
        sa.Column("name_ru", sa.Text(), nullable=False),
        sa.Column("name_en", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_cities"),
        schema=S,
    )
    op.bulk_insert(cities, [
        {"code": c, "name_uz_latn": a, "name_uz_cyrl": b, "name_ru": r, "name_en": e}
        for c, a, b, r, e in CITIES
    ])

    op.add_column("lyceums", sa.Column("dormitory_status", sa.String(10), nullable=False,
                                       server_default="unknown"), schema=S)
    op.add_column("lyceums", sa.Column("dormitory_description", sa.JSON(), nullable=False,
                                       server_default="{}"), schema=S)

    # Free-text city -> code, matched from the lyceum names where unambiguous.
    op.execute(f"UPDATE {S}.lyceums SET city = NULL")
    op.alter_column("lyceums", "city", type_=sa.String(50), schema=S)
    variants = {c: [_norm(x) for x in (a, b, r, e)] for c, a, b, r, e in CITIES}
    conn = op.get_bind()
    rows = conn.execute(sa.text(f"SELECT id, name_uz, name_ru, name_en FROM {S}.lyceums")).all()
    for row in rows:
        code = _match([row.name_uz, row.name_ru, row.name_en], variants)
        if code is not None:
            conn.execute(sa.text(f"UPDATE {S}.lyceums SET city = :c WHERE id = :i"),
                         {"c": code, "i": row.id})
    op.create_foreign_key("fk_lyceums_city_cities", "lyceums", "cities", ["city"], ["code"],
                          source_schema=S, referent_schema=S, ondelete="SET NULL")
    op.create_index("ix_lyceums_city", "lyceums", ["city"], schema=S)


def downgrade() -> None:
    op.drop_index("ix_lyceums_city", table_name="lyceums", schema=S)
    op.drop_constraint("fk_lyceums_city_cities", "lyceums", schema=S, type_="foreignkey")
    op.alter_column("lyceums", "city", type_=sa.String(100), schema=S)
    op.drop_column("lyceums", "dormitory_description", schema=S)
    op.drop_column("lyceums", "dormitory_status", schema=S)
    op.drop_table("cities", schema=S)
