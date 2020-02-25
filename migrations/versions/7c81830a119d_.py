"""empty message

Revision ID: 7c81830a119d
Revises: a70d4740fbc6
Create Date: 2019-12-23 13:23:34.812648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c81830a119d'
down_revision = 'a70d4740fbc6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reports', sa.Column('reporter_email', sa.String(length=128), nullable=False))
    op.create_unique_constraint('only one report per moderator', 'reports', ['application_id', 'reporter_email'])
    op.create_foreign_key(None, 'reports', 'accounts', ['reporter_email'], ['email'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'reports', type_='foreignkey')
    op.drop_constraint('only one report per moderator', 'reports', type_='unique')
    op.drop_column('reports', 'reporter_email')
    # ### end Alembic commands ###
