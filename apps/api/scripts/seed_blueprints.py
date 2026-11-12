"""Idempotently seed one *draft* official blueprint per academic-lyceum study field.

Source: 2027/2028 (same structure as 2026/2027) official spec "Akademik litseylarning ta'lim
yo'nalishlariga mos test sinovi o'tkaziladigan fanlar majmuasi, test topshiriqlari soni hamda
baholash mezonlari" (https://api-portal.gov.uz/uploads/7/2026/11/06/6c0662be-4823-a740-a09f-496c424f1f92_media_.pdf):
subject 1 = 20 q x 3.1, subject 2 = 20 q x 3.1, IQ = 20 q x 1.1 -> 60 q, max 146.
Duration: DTM rules give 2 hours for 60 test items (https://tuit.uz/post/eslatma) -> 120 min.

The blueprint code is the official field code; names (4 locales) are composed from the
subjects' own ``names`` plus the group name, e.g. "Matematika + Fizika (Aniq fanlar-1)".
Missing subjects are created; existing blueprints/subjects are never modified. Admin publishes.

Usage: DATABASE_URL=postgresql+asyncpg://... uv run python scripts/seed_blueprints.py
"""

import asyncio
import json
import os
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:pg@localhost:55432/dtmai")
LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
DURATION_MIN = 120
SUBJECT_Q, SUBJECT_W, IQ_Q, IQ_W = 20, 3.1, 20, 1.1

# Subjects created only when absent (code -> names). Existing: math, physics, history, iq, english.
NEW_SUBJECTS = {
    "foreign_language": ("Xorijiy til", "Хорижий тил", "Иностранный язык", "Foreign language"),
    "native_language": (
        "Ona tili va adabiyot",
        "Она тили ва адабиёт",
        "Родной язык и литература",
        "Native language and literature",
    ),
    "geography": ("Geografiya", "География", "География", "Geography"),
    "biology": ("Biologiya", "Биология", "Биология", "Biology"),
    "chemistry": ("Kimyo", "Кимё", "Химия", "Chemistry"),
    "law": ("Huquqshunoslik", "Ҳуқуқшунослик", "Правоведение", "Law"),
}

GROUPS = {
    "exact": ("Aniq fanlar", "Аниқ фанлар", "Точные науки", "Exact sciences"),
    "natural": ("Tabiiy fanlar", "Табиий фанлар", "Естественные науки", "Natural sciences"),
    "social": (
        "Ijtimoiy-gumanitar fanlar",
        "Ижтимоий-гуманитар фанлар",
        "Социально-гуманитарные науки",
        "Social sciences and humanities",
    ),
    "languages": ("Xorijiy tillar", "Хорижий тиллар", "Иностранные языки", "Foreign languages"),
}
DRAWING = (
    "Rasm va chizmachilik",
    "Расм ва чизмачилик",
    "Рисунок и черчение",
    "Drawing and technical drawing",
)

# code, group, number (None = unnumbered), subject1, subject2 (None = creative exam)
FIELDS = [
    ("3910001", "exact", 1, "math", "physics"),
    ("3910002", "exact", 2, "math", "foreign_language"),
    ("3910003", "exact", 3, "math", None),
    ("3910004", "exact", 4, "math", "native_language"),
    ("3910005", "exact", 5, "math", "geography"),
    ("3920001", "natural", 1, "biology", "chemistry"),
    ("3920002", "natural", 2, "chemistry", "math"),
    ("3930001", "social", 1, "native_language", "foreign_language"),
    ("3930002", "social", 2, "history", "foreign_language"),
    ("3930003", "social", 3, "native_language", "biology"),
    ("3930004", "social", 4, "history", "geography"),
    ("3930005", "social", 5, "law", "foreign_language"),
    ("3940000", "languages", None, "foreign_language", "native_language"),
]


def field_names(group: str, num: int | None, s1: dict, s2: dict | None) -> dict[str, str]:
    out = {}
    for i, loc in enumerate(LOCALES):
        second = s2[loc] if s2 else DRAWING[i]
        grp = GROUPS[group][i] + (f"-{num}" if num else "")
        out[loc] = f"{s1[loc]} + {second} ({grp})"
    return out


async def main() -> None:
    eng = create_async_engine(DB)
    async with eng.begin() as c:
        pos = (
            await c.execute(text("select coalesce(max(position), 0) from catalog.subjects"))
        ).scalar_one()
        for code, nm in NEW_SUBJECTS.items():
            pos += 1
            r = await c.execute(
                text(
                    "insert into catalog.subjects (id, code, names, weight, active, position) "
                    "values (:id, :code, cast(:names as jsonb), 1, true, :pos) "
                    "on conflict (code) do nothing"
                ),
                {
                    "id": uuid.uuid4(),
                    "code": code,
                    "names": json.dumps(dict(zip(LOCALES, nm))),
                    "pos": pos,
                },
            )
            print(f"subject {code}: {'created' if r.rowcount else 'exists'}")
        subs = {
            r.code: (r.id, r.names)
            for r in await c.execute(text("select id, code, names from catalog.subjects"))
        }
        for code, group, num, c1, c2 in FIELDS:
            names = field_names(group, num, subs[c1][1], subs[c2][1] if c2 else None)
            sections = [
                {
                    "subject_id": str(subs[c1][0]),
                    "topic_ids": [],
                    "type_ids": [],
                    "count": SUBJECT_Q,
                    "weight": SUBJECT_W,
                }
            ]
            if c2:
                sections.append(
                    {
                        "subject_id": str(subs[c2][0]),
                        "topic_ids": [],
                        "type_ids": [],
                        "count": SUBJECT_Q,
                        "weight": SUBJECT_W,
                    }
                )
            sections.append(
                {
                    "subject_id": str(subs["iq"][0]),
                    "topic_ids": [],
                    "type_ids": [],
                    "count": IQ_Q,
                    "weight": IQ_W,
                }
            )
            r = await c.execute(
                text(
                    "insert into catalog.blueprints (id, code, version, names, kind, sections, duration_min, status) "
                    "values (:id, :code, 0, cast(:names as jsonb), 'official', cast(:sections as jsonb), :dur, 'draft') "
                    "on conflict (code, version) do nothing"
                ),
                {
                    "id": uuid.uuid4(),
                    "code": code,
                    "names": json.dumps(names, ensure_ascii=False),
                    "sections": json.dumps(sections),
                    "dur": DURATION_MIN,
                },
            )
            print(f"blueprint {code}: {'created' if r.rowcount else 'exists'}  {names['uz-Latn']}")
    await eng.dispose()


if __name__ == "__main__":
    asyncio.run(main())
