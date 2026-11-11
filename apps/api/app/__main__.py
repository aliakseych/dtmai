import os
import sys

USAGE = "usage: python -m app api|worker|scheduler|migrate|seed|ingest <path> --source <code>|promote <email> [role ...]"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "ingest":
        from app.modules.labeling.cli import main as ingest_main

        return ingest_main(argv[1:])
    if argv and argv[0] == "promote":
        from app.modules.identity.cli import main as promote_main

        return promote_main(argv[1:])
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
            os.execvp("taskiq", ["taskiq", "worker", "app.bootstrap.tasks:broker", "app.bootstrap.tasks"])
        case "scheduler":
            os.execvp("taskiq", ["taskiq", "scheduler", "app.bootstrap.tasks:scheduler", "app.bootstrap.tasks"])
        case "migrate":
            from alembic.config import main as alembic_main

            alembic_main(argv=["upgrade", "heads"])
        case "seed":
            from app.modules.catalog.seed import main as seed_main

            return seed_main()
        case _:
            print(USAGE, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
