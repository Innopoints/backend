"""empty message

Revision ID: 133713371338
Revises: 563841f14d37
Create Date: 2019-12-26 21:10:14.032751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '133713371338'
down_revision = '1d13ba6044e3'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE notificationtype RENAME TO notificationtype_old;")
    op.execute("CREATE TYPE notificationtype AS enum('purchase_status_changed', 'new_arrivals', 'claim_innopoints', 'application_status_changed', 'service', 'project_review_status_changed', 'all_feedback_in', 'out_of_stock', 'new_purchase', 'project_review_requested', 'added_as_moderator');")
    op.execute("ALTER TABLE notifications ALTER COLUMN type TYPE notificationtype USING type::text::notificationtype;")
    op.execute("DROP TYPE notificationtype_old;")



def downgrade():
    op.execute("ALTER TYPE notificationtype RENAME TO notificationtype_old;")
    op.execute("CREATE TYPE notificationtype AS enum('purchase_ready', 'new_arrivals', 'claim_ipts', 'apl_accept', 'apl_reject', 'service', 'act_table_reject', 'all_feedback_in', 'out_of_stock', 'new_purchase', 'proj_final_review');")
    op.execute("ALTER TABLE notifications ALTER COLUMN type TYPE notificationtype USING type::text::notificationtype;")
    op.execute("DROP TYPE notificationtype_old;")
