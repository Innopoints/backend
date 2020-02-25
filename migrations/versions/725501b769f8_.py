"""empty message

Revision ID: 725501b769f8
Revises: 687698d9105f
Create Date: 2019-12-23 23:04:43.715683

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '725501b769f8'
down_revision = '687698d9105f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('only one report per moderator', 'reports', type_='unique')
    op.drop_constraint('reports_application_id_key', 'reports', type_='unique')
    # ### end Alembic commands ###
    op.create_primary_key('pk_reports', 'reports', ['application_id', 'reporter_email'])


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        'reports_application_id_key', 'reports', ['application_id']
    )
    op.create_unique_constraint(
        'only one report per moderator', 'reports', ['application_id', 'reporter_email']
    )
    # ### end Alembic commands ###
    op.drop_constraint('pk_reports', 'reports', type_='primary')
