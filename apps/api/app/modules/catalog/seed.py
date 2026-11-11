"""Idempotent catalog seed: `python -m app.modules.catalog.seed`.

Creates the five launch subjects, base question types, question bases and topics harvested
from data/categories.json (override with CATEGORIES_JSON). Re-running adds only what is missing.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.facade import service
from app.shared.db import get_sessionmaker

SUBJECTS: list[tuple[str, dict[str, str]]] = [
    ("math", {"uz-Latn": "Matematika", "uz-Cyrl": "Математика", "ru": "Математика", "en": "Mathematics"}),
    ("english", {"uz-Latn": "Ingliz tili", "uz-Cyrl": "Инглиз тили", "ru": "Английский язык", "en": "English"}),
    ("iq", {"uz-Latn": "IQ (mantiqiy fikrlash)", "uz-Cyrl": "IQ (мантиқий фикрлаш)", "ru": "IQ (логика)", "en": "IQ / Logic"}),
    ("history", {"uz-Latn": "Tarix", "uz-Cyrl": "Тарих", "ru": "История", "en": "History"}),
    ("physics", {"uz-Latn": "Fizika", "uz-Cyrl": "Физика", "ru": "Физика", "en": "Physics"}),
]

_CHOICE = {"option_count": 4, "label_scheme": "latin"}
TYPES: list[dict[str, Any]] = [
    {"code": "mcq_single_4", "kind": "single_choice", "names": {"en": "Multiple choice (4)", "ru": "Тест (4 варианта)", "uz-Latn": "Test (4 variant)", "uz-Cyrl": "Тест (4 вариант)"}, "config": _CHOICE},
    {"code": "mcq_word_pair", "kind": "single_choice", "names": {"en": "Word-pair choice", "ru": "Пара слов", "uz-Latn": "So'z juftligi", "uz-Cyrl": "Сўз жуфтлиги"}, "config": {**_CHOICE, "option_style": "word_pair"}},
    {"code": "image_stem_mcq", "kind": "single_choice", "names": {"en": "Image question", "ru": "Вопрос с рисунком", "uz-Latn": "Rasmli savol", "uz-Cyrl": "Расмли савол"}, "config": {**_CHOICE, "image_stem": True}},
    {"code": "numeric_input", "kind": "numeric", "names": {"en": "Numeric answer", "ru": "Числовой ответ", "uz-Latn": "Raqamli javob", "uz-Cyrl": "Рақамли жавоб"}, "config": {}},
    {"code": "reading_group", "kind": "passage_group", "names": {"en": "Reading passage", "ru": "Текст с вопросами", "uz-Latn": "Matn va savollar", "uz-Cyrl": "Матн ва саволлар"}, "config": {}},
]

BASES: list[dict[str, Any]] = [
    {"code": "previous_years", "kind": "previous_year", "names": {"en": "Previous-year exams", "ru": "Экзамены прошлых лет", "uz-Latn": "Oldingi yillar imtihonlari", "uz-Cyrl": "Олдинги йиллар имтиҳонлари"}},
    {"code": "bluebook", "kind": "bluebook", "names": {"en": "Bluebook-style practice papers", "ru": "Пробные работы (Bluebook)", "uz-Latn": "Bluebook uslubidagi mashq", "uz-Cyrl": "Bluebook услубидаги машқ"}},
    {"code": "ai_generated", "kind": "ai_generated", "names": {"en": "AI-generated", "ru": "Созданные ИИ", "uz-Latn": "AI yaratgan", "uz-Cyrl": "AI яратган"}},
    {"code": "harvested", "kind": "harvested", "names": {"en": "Harvested bank", "ru": "Общий банк вопросов", "uz-Latn": "Umumiy savollar banki", "uz-Cyrl": "Умумий саволлар банки"}},
]

_CATEGORY_SUBJECT = {"MATH": ("math", "ru"), "ENGLISH": ("english", "en")}


def categories_path() -> Path:
    env = os.environ.get("CATEGORIES_JSON")
    return Path(env) if env else Path(__file__).resolve().parents[5] / "data" / "categories.json"


async def seed(session: AsyncSession) -> dict[str, int]:
    svc = service(session)
    added = {"subjects": 0, "types": 0, "bases": 0, "topics": 0}
    subj_ids: dict[str, Any] = {r["code"]: r["id"] for r in await svc.repo.list("subject")}
    for code, names in SUBJECTS:
        if code not in subj_ids:
            subj_ids[code] = (await svc.create("subject", {"code": code, "names": names}, "seed"))["id"]
            added["subjects"] += 1
    have = {r["code"] for r in await svc.repo.list("question_type")}
    for t in TYPES:
        if t["code"] not in have:
            await svc.create("question_type", dict(t), "seed")
            added["types"] += 1
    have = {r["code"] for r in await svc.repo.list("question_base")}
    for b in BASES:
        if b["code"] not in have:
            await svc.create("question_base", dict(b), "seed")
            added["bases"] += 1
    path = categories_path()
    if path.is_file():
        for item in json.loads(path.read_text(encoding="utf-8")):
            mapped = _CATEGORY_SUBJECT.get(item["subject"])
            if not mapped:
                continue
            code, loc = mapped
            existing = {tuple(sorted(t["names"].items())) for t in await svc.repo.list("topic", subject_id=subj_ids[code])}
            names = {loc: item["name"]}
            if tuple(sorted(names.items())) not in existing:
                await svc.create("topic", {"subject_id": subj_ids[code], "names": names}, "seed")
                added["topics"] += 1
    else:
        print(f"categories file not found: {path} (topics skipped)")
    return added


async def _run() -> None:
    async with get_sessionmaker()() as session:
        result = await seed(session)
        await session.commit()
    print("seeded:", result)


def main() -> int:
    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
