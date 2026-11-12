from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.modules.gamification.infrastructure import orm
from app.modules.gamification.infrastructure.repositories import not_guest


def test_not_guest_predicate_targets_pure_guest_role() -> None:
    q = select(orm.UserStatsRow.user_id).where(not_guest(orm.UserStatsRow.user_id))
    sql = str(q.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "identity.users" in sql
    assert "NOT (EXISTS" in sql.replace("\n", " ")
    assert "'guest'" in sql and "'student'" in sql
