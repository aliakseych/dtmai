"""English names for edu.uz education languages (the source ships none).

Revision ID: lyceums_0009
Revises: lyceums_0008
"""

from alembic import op

revision = "lyceums_0009"
down_revision = "lyceums_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE lyceums.education_languages AS l SET name_en = v.name
        FROM (VALUES
        ('11', 'Uzbek language'),
        ('12', 'Russian language'),
        ('13', 'Karakalpak language'),
        ('14', 'English language'),
        ('15', 'Tajik language'),
        ('16', 'Kazakh language'),
        ('17', 'Turkmen language'),
        ('18', 'Korean language'),
        ('19', 'German language'),
        ('20', 'French language'),
        ('21', 'Turkish language'),
        ('22', 'Kyrgyz language')
        ) AS v(code, name)
        WHERE l.code = v.code AND coalesce(l.name_en, '') = ''
        """
    )


def downgrade() -> None:
    pass
