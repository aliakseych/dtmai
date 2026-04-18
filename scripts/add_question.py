"""
Manually insert a question from JSON when AI output fails to parse.

Reads JSON from a file or stdin, validates it against AIQuestionResponse,
then inserts the question into MongoDB.

Usage:
    # From a file:
    python -m scripts.add_question --source mock1 --subject math question.json

    # From stdin (paste JSON, then Ctrl+D):
    python -m scripts.add_question --source mock1 --subject math

    # Dry-run (validate only, no DB write):
    python -m scripts.add_question --source mock1 --subject math question.json --dry-run

Expected JSON shape (same as AI output):
{
  "category": "Квадратный корень",
  "level": "ORIGINAL",
  "question_text": "Вычислите: ...",
  "answers": ["1", "2", "3", "4"],
  "correct_answer": "2",
  "solution_steps": [
    {"action": "...", "formula": "...", "explanation": "..."}
  ]
}
"""
import asyncio
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from uuid6 import uuid7

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.questions import QuestionRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.interfaces.ai.schemas import AIQuestionResponse
from src.services.category_service import CategoryService
from src.services.question_service import FOLDER_SUBJECT_MAP, _text_hash
from src.settings import settings


def _parse_args() -> tuple[str, str, Path | None, bool]:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    source = subject = None
    positional = []

    i = 0
    while i < len(args):
        if args[i] in ("--source", "--subject") and i + 1 < len(args):
            if args[i] == "--source":
                source = args[i + 1]
            else:
                subject = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    if not source or not subject:
        print("Usage: python -m scripts.add_question --source <name> --subject <subject> [file.json] [--dry-run]")
        print(f"  --subject: one of {list(FOLDER_SUBJECT_MAP.keys())}")
        sys.exit(1)

    file_path = Path(positional[0]) if positional else None
    return source, subject, file_path, dry_run


def _load_json(file_path: Path | None) -> dict:
    if file_path:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            sys.exit(1)
        raw = file_path.read_text(encoding="utf-8")
    else:
        print("Paste JSON below, then press Ctrl+D (or Ctrl+Z on Windows):")
        raw = sys.stdin.read()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"\nInvalid JSON: {e}")
        sys.exit(1)


def _validate(data: dict) -> AIQuestionResponse:
    try:
        return AIQuestionResponse.model_validate(data)
    except ValidationError as e:
        print("\nValidation failed:")
        for err in e.errors():
            field = " → ".join(str(loc) for loc in err["loc"])
            print(f"  [{field}] {err['msg']}")
        sys.exit(1)


async def main():
    source_name, subject_str, file_path, dry_run = _parse_args()

    subject = FOLDER_SUBJECT_MAP.get(subject_str.lower())
    if subject is None:
        print(f"Unknown subject '{subject_str}'. Known: {list(FOLDER_SUBJECT_MAP.keys())}")
        sys.exit(1)

    data = _load_json(file_path)
    result = _validate(data)

    print(f"\nParsed OK:")
    print(f"  Category:  {result.category}")
    print(f"  Level:     {result.level.value}")
    print(f"  Question:  {result.question_text[:80]}{'...' if len(result.question_text) > 80 else ''}")
    print(f"  Answers:   {result.answers}")
    print(f"  Correct:   {result.correct_answer}")
    print(f"  Steps:     {len(result.solution_steps or [])} step(s)")

    if dry_run:
        print("\n[DRY RUN] Validation passed. No DB write.")
        return

    mongo = MongoClient(settings.MONGO_URI, settings.MONGO_DB_NAME)
    category_repo = CategoryRepository(mongo)
    question_repo = QuestionRepository(mongo)
    source_repo = SourceRepository(mongo)
    category_service = CategoryService(category_repo)

    text_hash = _text_hash(result.question_text)
    if await question_repo.exists_by_text_hash(text_hash):
        print("\nSkipped: a question with this text already exists in the database.")
        return

    source_id = await source_repo.get_or_create(source_name, str(uuid7()))

    existing_cats = await category_repo.get_by_subject(subject.value)
    category_id, _ = await category_service.resolve(result.category, subject.value, existing_cats)

    question_doc = {
        "_id": str(uuid7()),
        "subject": subject.value,
        "category_id": category_id,
        "source_id": source_id,
        "level": result.level.value,
        "question": result.question_text,
        "text_hash": text_hash,
        "answers": result.answers,
        "correct_answer": result.correct_answer,
        "solution_steps": (
            [s.model_dump() for s in result.solution_steps]
            if result.solution_steps else None
        ),
    }
    await question_repo.create(question_doc)
    print(f"\nInserted question (id={question_doc['_id']})")


if __name__ == "__main__":
    asyncio.run(main())
