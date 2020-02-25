"""empty message

Revision ID: 95c2a0076d4c
Revises: 133713371339
Create Date: 2020-01-05 17:03:59.082671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "95c2a0076d4c"
down_revision = "133713371339"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "name is unique inside a project", "activities", ["name", "project_id"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("name is unique inside a project", "activities", type_="unique")
    # ### end Alembic commands ###
