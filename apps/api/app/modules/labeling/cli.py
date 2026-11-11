import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from app.modules.ai.wiring import get_gateway
from app.modules.labeling.application.classify import classify_topics
from app.modules.labeling.application.ingest import IngestService
from app.modules.labeling.infrastructure import catalog_adapter
from app.modules.labeling.tasks import solve_many
from app.shared.db import get_sessionmaker


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m app ingest")
    p.add_argument("path", help="local file/dir or s3://bucket/prefix")
    p.add_argument("--source", required=True, help="source code, e.g. dtm-2023")
    p.add_argument("--source-name")
    p.add_argument("--year", type=int)
    p.add_argument("--subject", help="subject code (default: guessed from the directory name)")
    p.add_argument("--subject-id", type=UUID)
    p.add_argument("--language", required=True, help="content language of the files (uz|ru)")
    p.add_argument("--base", help="paper/mock name")
    p.add_argument("--key", action="store_true", help="files contain an official answer key")
    p.add_argument("--topic-id", type=UUID)
    p.add_argument("--type", action="append", default=[], metavar="KIND=UUID")
    p.add_argument("--no-solve", action="store_true", help="skip the auto-solve pass")
    return p


async def run(argv: list[str]) -> int:
    a = build_parser().parse_args(argv)
    async with get_sessionmaker()() as session:
        subject_id = a.subject_id
        if subject_id is None:
            subjects = await catalog_adapter.list_subjects(session)
            wanted = (a.subject or Path(a.path.rstrip("/")).parent.name or "").lower()
            hit = next((s for s in subjects if s.code.lower() == wanted), None) or next(
                (s for s in subjects if s.code.lower() in a.path.lower()), None
            )
            if hit is None:
                print("cannot resolve subject; pass --subject or --subject-id")
                return 2
            subject_id = hit.id
        gw = get_gateway()
        svc = IngestService(session, gw)
        batch = await svc.create_batch(
            root=a.path, source_code=a.source, source_name=a.source_name, source_year=a.year,
            subject_id=subject_id, language=a.language, base=a.base, has_answer_key=a.key, topic_id=a.topic_id,
            type_ids={k: UUID(v) for k, _, v in (t.partition("=") for t in a.type)}, created_by=None,
        )
        await session.commit()
        created = await svc.run(batch.id)
        print(f"batch {batch.id}: {batch.status}, {len(created)} questions, {batch.error or 'ok'}")
        if not a.no_solve:
            await solve_many(created, "ingestion")
    return 0 if batch.status == "done" else 1


def main(argv: list[str]) -> int:
    if argv and argv[0] == "solve":
        return asyncio.run(solve_drafts(argv[1:]))
    if argv and argv[0] == "reclassify":
        return asyncio.run(reclassify(argv[1:]))
    return asyncio.run(run(argv))


async def reclassify(argv: list[str]) -> int:
    """`reclassify --subject <code>`: re-assign every question of the subject to its best-matching topic."""
    p = argparse.ArgumentParser(prog="python -m app ingest reclassify")
    p.add_argument("--subject", required=True)
    a = p.parse_args(argv)
    async with get_sessionmaker()() as session:
        hit = next((s for s in await catalog_adapter.list_subjects(session) if s.code.lower() == a.subject.lower()), None)
        if hit is None:
            print("unknown subject")
            return 2
        rows = await session.execute(
            text("SELECT id FROM bank.questions WHERE subject_id=:s ORDER BY created_at, id"), {"s": hit.id}
        )
        changed = await classify_topics(session, get_gateway(), subject_id=hit.id, question_ids=[r[0] for r in rows])
        print(f"{len(changed)} question(s) re-assigned")
    return 0


async def solve_drafts(argv: list[str]) -> int:
    """`solve --subject <code>`: run the auto-solve pass over every still-draft question of the subject."""
    p = argparse.ArgumentParser(prog="python -m app ingest solve")
    p.add_argument("--subject", required=True)
    a = p.parse_args(argv)
    async with get_sessionmaker()() as session:
        hit = next((s for s in await catalog_adapter.list_subjects(session) if s.code.lower() == a.subject.lower()), None)
        if hit is None:
            print("unknown subject")
            return 2
        rows = await session.execute(
            text("SELECT id FROM bank.questions WHERE subject_id=:s AND status='draft' ORDER BY created_at, id"),
            {"s": hit.id},
        )
        ids = [r[0] for r in rows]
        done = await solve_many(ids, "ingestion")
        print(f"solved {done}/{len(ids)} draft question(s)")
    return 0
