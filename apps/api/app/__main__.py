import os
import sys

USAGE = (
    "usage: python -m app api|worker|scheduler|migrate|seed|seed-exam-info"
    "|ingest <path> --source <code>|promote <email> [role ...]|import-lyceum-admission"
)


def main(argv: list[str]) -> int:
    if argv and argv[0] == "ingest":
        from app.modules.labeling.cli import main as ingest_main

        return ingest_main(argv[1:])
    if argv and argv[0] == "promote":
        from app.modules.identity.cli import main as promote_main

        return promote_main(argv[1:])
    if argv and argv[0] == "import-lyceum-admission":
        from app.modules.lyceums.cli import main as admission_main

        return admission_main(argv[1:])
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 2
    match argv[0]:
        case "api":
            import uvicorn

            uvicorn.run(
                "app.bootstrap.http:create_app",
                factory=True,
                host=os.environ.get("HOST", "0.0.0.0"),  # noqa: S104
                port=int(os.environ.get("PORT", "8000")),
                proxy_headers=True,
                forwarded_allow_ips="*",
            )
        case "worker":
            os.execvp(
                "taskiq", ["taskiq", "worker", "app.bootstrap.tasks:broker", "app.bootstrap.tasks"]
            )
        case "scheduler":
            os.execvp(
                "taskiq",
                ["taskiq", "scheduler", "app.bootstrap.tasks:scheduler", "app.bootstrap.tasks"],
            )
        case "migrate":
            from alembic.config import main as alembic_main

            alembic_main(argv=["upgrade", "heads"])
            # Insert-only seeds: never overwrite admin edits, safe on every deploy.
            # Catalog first: exam sections link to catalog subjects by code.
            from app.modules.catalog.seed import main as seed_catalog_main
            from app.modules.exam_info.infrastructure.seed import main as seed_exam_info_main

            return seed_catalog_main() or seed_exam_info_main()
        case "seed":
            from app.modules.catalog.seed import main as seed_main

            return seed_main()
        case "seed-exam-info":
            from app.modules.exam_info.infrastructure.seed import main as seed_exam_info_main

            return seed_exam_info_main()
        case _:
            print(USAGE, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
