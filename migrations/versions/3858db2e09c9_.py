"""empty message

Revision ID: 3858db2e09c9
Revises: 0e1c9ef5e84a
Create Date: 2020-03-24 13:21:31.897183

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3858db2e09c9'
down_revision = '0e1c9ef5e84a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('transactions_feedback_id_fkey', 'transactions', type_='foreignkey')
    op.create_foreign_key(None, 'transactions', 'feedback', ['feedback_id'], ['application_id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.create_foreign_key('transactions_feedback_id_fkey', 'transactions', 'feedback', ['feedback_id'], ['application_id'], ondelete='CASCADE')
    # ### end Alembic commands ###
