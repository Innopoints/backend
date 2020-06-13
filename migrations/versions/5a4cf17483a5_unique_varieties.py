"""Add the 'unique varieties' index

Revision ID: 5a4cf17483a5
Revises: 22ec8260152c
Create Date: 2020-06-13 19:10:05.833296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a4cf17483a5'
down_revision = '22ec8260152c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('unique varieties', 'varieties',
                    ['product_id',
                     sa.text("coalesce(color, '')"),
                     sa.text("coalesce(size, '')")],
                    unique=True)

def downgrade():
    op.drop_index('unique varieties', 'varieties')
