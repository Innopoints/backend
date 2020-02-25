"""empty message

Revision ID: ed3e8a2fe2dd
Revises: 7c81830a119d
Create Date: 2019-12-23 15:30:30.534886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed3e8a2fe2dd'
down_revision = '7c81830a119d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name='activities',
        column_name='start_date',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        table_name='activities',
        column_name='end_date',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        table_name='applications',
        column_name='application_time',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        table_name='products',
        column_name='addition_time',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        table_name='projects',
        column_name='creation_time',
        type_=sa.DateTime(timezone=True),
    )
    op.alter_column(
        table_name='stock_changes', column_name='time', type_=sa.DateTime(timezone=True)
    )


def downgrade():
    op.alter_column(
        table_name='activities', column_name='start_date', type_=sa.DateTime()
    )
    op.alter_column(
        table_name='activities', column_name='end_date', type_=sa.DateTime()
    )
