"""empty message

Revision ID: 297d3ef73ef1
Revises: 2664aaf602ab
Create Date: 2020-01-05 16:35:14.032751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '297d3ef73ef1'
down_revision = '2664aaf602ab'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE notificationtype RENAME TO notificationtype_old;")
    op.execute(
        "CREATE TYPE notificationtype AS enum('purchase_status_changed', 'new_arrivals', 'claim_innopoints', 'application_status_changed', 'service', 'manual_transaction', 'project_review_status_changed', 'all_feedback_in', 'out_of_stock', 'new_purchase', 'project_review_requested', 'added_as_moderator');"
    )
    op.execute(
        "ALTER TABLE notifications ALTER COLUMN type TYPE notificationtype USING type::text::notificationtype;"
    )
    op.execute("DROP TYPE notificationtype_old;")


def downgrade():
    op.execute("ALTER TYPE notificationtype RENAME TO notificationtype_old;")
    op.execute(
        "CREATE TYPE notificationtype AS enum('purchase_status_changed', 'new_arrivals', 'claim_innopoints', 'application_status_changed', 'service', 'project_review_status_changed', 'all_feedback_in', 'out_of_stock', 'new_purchase', 'project_review_requested', 'added_as_moderator');"
    )
    op.execute(
        "ALTER TABLE notifications ALTER COLUMN type TYPE notificationtype USING type::text::notificationtype;"
    )
    op.execute("DROP TYPE notificationtype_old;")
