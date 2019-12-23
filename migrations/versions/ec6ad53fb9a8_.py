"""empty message

Revision ID: ec6ad53fb9a8
Revises: 725501b769f8
Create Date: 2019-12-24 01:01:30.124268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec6ad53fb9a8'
down_revision = '725501b769f8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_check_constraint('reward policy', 'activities', '(fixed_reward AND working_hours = 1) OR (NOT fixed_reward AND reward_rate = 70)')


def downgrade():
    op.drop_constraint('reward policy', 'activities', type_='check')
