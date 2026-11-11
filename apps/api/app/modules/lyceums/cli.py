import asyncio

from app.modules.lyceums.wiring import build_admission_service
from app.shared.db import get_sessionmaker


async def _run() -> int:
    async with get_sessionmaker()() as session:
        report = await build_admission_service(session).import_seed()
        await session.commit()
    print(
        f"matched plan={report.matched['plan']} contact={report.matched['contact']}; "
        f"plan rows written={report.plan_rows_written}, contacts written={report.contacts_written}, "
        f"skipped admin edits={report.skipped_admin_edits}, skipped deleted={report.skipped_deleted}"
    )
    for u in report.unmatched:
        tag = "ambiguous" if u.ambiguous else "unmatched"
        print(f"{tag} {u.kind} #{u.ref}: {u.name}")
    return 0


def main(argv: list[str]) -> int:
    if argv:
        print("usage: python -m app import-lyceum-admission")
        return 2
    return asyncio.run(_run())
