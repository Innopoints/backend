"""empty message

Revision ID: 0e1c9ef5e84a
Revises: fb2d5a9830a4
Create Date: 2020-02-04 13:45:02.677474

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e1c9ef5e84a'
down_revision = 'fb2d5a9830a4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(None, 'feedback', 'applications', ['application_id'], ['id'], ondelete='CASCADE')
    op.drop_column('static_files', 'namespace')
    op.drop_constraint('transactions_feedback_id_fkey', 'transactions', type_='foreignkey')
    op.create_foreign_key(None, 'transactions', 'feedback', ['feedback_id'], ['application_id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'transactions', type_='foreignkey')
    op.create_foreign_key('transactions_feedback_id_fkey', 'transactions', 'feedback', ['feedback_id'], ['application_id'])
    op.add_column('static_files', sa.Column('namespace', sa.VARCHAR(length=64), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'feedback', type_='foreignkey')
    op.create_foreign_key('feedback_application_id_fkey', 'feedback', 'applications', ['application_id'], ['id'])
    # ### end Alembic commands ###
