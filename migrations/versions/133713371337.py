"""empty message

Revision ID: 1d3051931992
Revises: f3c0d5e15dc9
Create Date: 2019-12-14 20:44:14.032751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '133713371337'
down_revision = '1d3051931992'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('unique_varieties', 'varieties', ['product_id', sa.text("coalesce(color_value, '')"), sa.text("coalesce(size_id, '')")], unique=True)


def downgrade():
    op.drop_index('unique_varieties', 'varieties')
