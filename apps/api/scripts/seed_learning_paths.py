"""Idempotently publish a learning path per (subject, language) from verified questions.

Creates path -> unit -> lessons through the admin HTTP API. Topics with verified
questions are grouped (in position order) into lessons whose verified pool reaches
``max(CONTENT_MIN_POOL, QUESTION_COUNT)``; a smaller remainder merges into the last
lesson. Subjects whose total pool is below that never get a visible lesson, so they
are skipped. Re-running only adds missing lessons and (re)publishes paths.

Usage: API_URL=http://localhost:8000 DATABASE_URL=postgresql+asyncpg://... \
       ADMIN_EMAIL=... ADMIN_PASSWORD=... uv run python scripts/seed_learning_paths.py
"""

import asyncio
import os

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

API = os.environ.get("API_URL", "http://localhost:8000")
DB = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:pg@localhost:55432/dtmai")
EMAIL = os.environ.get("ADMIN_EMAIL", "admin@dtm-ai.uz")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "AdminPass123!")
MIN_POOL = int(os.environ.get("CONTENT_MIN_POOL", "30"))
QUESTION_COUNT = int(os.environ.get("QUESTION_COUNT", "10"))
LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")

POOLS = """
select s.id sid, s.names sn, q.language, t.id tid, t.names tn, count(*) n
from bank.questions q
join catalog.subjects s on s.id = q.subject_id
join catalog.topics t on t.id = q.topic_id
where q.status = 'verified' and s.active and t.active
group by s.id, s.names, s.position, q.language, t.id, t.names, t.position
order by s.position, q.language, t.position, t.id
"""


def group_topics(rows: list[dict], need: int) -> list[list[dict]]:
    groups: list[list[dict]] = [[]]
    acc = 0
    for r in rows:
        groups[-1].append(r)
        acc += r["n"]
        if acc >= need:
            groups.append([])
            acc = 0
    if not groups[-1]:
        groups.pop()
    elif len(groups) > 1:
        groups[-2].extend(groups.pop())
    return groups


def lesson_names(group: list[dict], idx: int) -> dict[str, str]:
    return {
        loc: (group[0]["tn"].get(loc) or group[0]["tn"].get("en") or "")
        + (f" +{len(group) - 1}" if len(group) > 1 else "")
        for loc in LOCALES
    } | {"_idx": str(idx)}


async def main() -> None:
    eng = create_async_engine(DB)
    async with eng.connect() as c:
        rows = [dict(r._mapping) for r in await c.execute(text(POOLS))]
    await eng.dispose()
    need = max(MIN_POOL, QUESTION_COUNT)
    by_key: dict[tuple, list[dict]] = {}
    for r in rows:
        by_key.setdefault((str(r["sid"]), r["language"]), []).append(r)

    async with httpx.AsyncClient(base_url=API, timeout=30) as http:
        tok = (
            await http.post("/v1/identity/login", json={"email": EMAIL, "password": PASSWORD})
        ).json()["access_token"]
        http.headers["Authorization"] = f"Bearer {tok}"
        base = "/v1/admin/catalog"

        async def get(p: str, **params):
            r = await http.get(base + p, params=params)
            r.raise_for_status()
            return r.json()

        async def post(p: str, body: dict):
            r = await http.post(base + p, json=body)
            r.raise_for_status()
            return r.json()

        for (sid, lang), trs in by_key.items():
            total = sum(t["n"] for t in trs)
            code = trs[0]["sn"].get("en")
            if total < need:
                print(f"skip {code}/{lang}: verified pool {total} < {need}")
                continue
            paths = [p for p in await get("/paths", subject_id=sid) if p["language"] == lang]
            path = (
                paths[0]
                if paths
                else await post(
                    "/paths",
                    {"subject_id": sid, "language": lang, "names": trs[0]["sn"]},
                )
            )
            units = [u for u in await get("/units", path_id=path["id"])]
            unit = (
                units[0]
                if units
                else await post("/units", {"path_id": path["id"], "names": trs[0]["sn"]})
            )
            existing = {
                tuple(sorted(le["topic_ids"])) for le in await get("/lessons", unit_id=unit["id"])
            }
            for i, g in enumerate(group_topics(trs, need), 1):
                tids = [str(t["tid"]) for t in g]
                if tuple(sorted(tids)) in existing:
                    continue
                names = lesson_names(g, i)
                names.pop("_idx")
                await post(
                    "/lessons",
                    {
                        "unit_id": unit["id"],
                        "names": names,
                        "topic_ids": tids,
                        "question_count": QUESTION_COUNT,
                    },
                )
            await post(f"/paths/{path['id']}/publish", {})
            print(f"published {code}/{lang}: pool {total}")


if __name__ == "__main__":
    asyncio.run(main())
