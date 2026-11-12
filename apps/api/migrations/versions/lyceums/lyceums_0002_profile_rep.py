"""lyceums: profile fields, rep memberships, posts

Revision ID: lyceums_0002
Revises: lyceums_0001
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "lyceums_0002"
down_revision = "lyceums_0001"
branch_labels = None
depends_on = None

S = "lyceums"


def upgrade() -> None:
    text_arr = postgresql.ARRAY(sa.Text())
    for name, col_type, default in (
        ("logo_url", sa.Text(), None),
        ("campus_photo_url", sa.Text(), None),
        ("gallery_urls", text_arr, "{}"),
        ("description", sa.JSON(), "{}"),
        ("courses", text_arr, "{}"),
        ("university_name", sa.Text(), None),
        ("city", sa.String(100), None),
        ("website", sa.Text(), None),
        ("contacts", sa.JSON(), "{}"),
        ("verified_rep", sa.Boolean(), "false"),
    ):
        op.add_column(
            "lyceums",
            sa.Column(name, col_type, nullable=default is None, server_default=default),
            schema=S,
        )
    op.create_table(
        "rep_memberships",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lyceum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("user_id", "lyceum_id", name="pk_rep_memberships"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"],
            [f"{S}.lyceums.id"],
            ondelete="CASCADE",
            name="fk_rep_memberships_lyceum_id_lyceums",
        ),
        schema=S,
    )
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lyceum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("link", sa.Text()),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("reject_reason", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_posts"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"],
            [f"{S}.lyceums.id"],
            ondelete="CASCADE",
            name="fk_posts_lyceum_id_lyceums",
        ),
        schema=S,
    )
    op.create_index("ix_posts_lyceum_id", "posts", ["lyceum_id"], schema=S)
    op.create_index("ix_posts_status", "posts", ["status"], schema=S)


def downgrade() -> None:
    op.drop_table("posts", schema=S)
    op.drop_table("rep_memberships", schema=S)
    for name in (
        "verified_rep",
        "contacts",
        "website",
        "city",
        "university_name",
        "courses",
        "description",
        "gallery_urls",
        "campus_photo_url",
        "logo_url",
    ):
        op.drop_column("lyceums", name, schema=S)
