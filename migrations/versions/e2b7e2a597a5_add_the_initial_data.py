"""Add the initial data

Revision ID: e2b7e2a597a5
Revises: bdeeeacbec4d
Create Date: 2020-04-15 18:53:29.664474

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2b7e2a597a5'
down_revision = 'bdeeeacbec4d'
branch_labels = None
depends_on = None


def upgrade():
    sizes_table = sa.sql.table(
        'sizes',
        sa.sql.column('value', sa.String),
    )

    colors_table = sa.sql.table(
        'colors',
        sa.sql.column('value', sa.String),
    )

    competences_table = sa.sql.table(
        'competences',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('name', sa.String),
    )

    op.bulk_insert(
        sizes_table,
        [{'value': value} for value in ('XS', 'S', 'M', 'L', 'XL', 'XXL')]
    )

    op.bulk_insert(
        colors_table,
        [{'value': value} for value in (
            '000000', 'A7A7A7', 'FFFFFF', 'DA1919', 'F7A222', 'F3EA15',
        	'387800', '26A1D3', '1A17D5', '060376', 'C617D5', 'EE9999',
        )]
    )

    op.bulk_insert(
        competences_table,
        [{'id': id, 'name': value} for id, value in enumerate(
            ('Teamwork & Cooperation',
             'Healthy Lifestyle & Wellbeing',
             'Communication',
             'Digital Grammar',
             'Learning to Learn',
             'Proactivity',
             'Critical Thinking',
             'Civil Competence',
             'Creativity & Innovation'),
            start=1,
        )]
    )


def downgrade():
    op.execute('DELETE FROM sizes')
    op.execute('DELETE FROM colors')
    op.execute('DELETE FROM competences')
