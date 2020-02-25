"""empty message

Revision ID: 912d0366a555
Revises: 2592727793d4
Create Date: 2019-12-13 16:18:40.294800

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "912d0366a555"
down_revision = "2592727793d4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "activity_competence_activity_id_fkey",
        "activity_competence",
        type_="foreignkey",
    )
    op.drop_constraint(
        "activity_competence_competence_id_fkey",
        "activity_competence",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "activity_competence",
        "activities",
        ["activity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        None,
        "activity_competence",
        "competences",
        ["competence_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "feedback_competence_competence_id_fkey",
        "feedback_competence",
        type_="foreignkey",
    )
    op.drop_constraint(
        "feedback_competence_feedback_id_fkey",
        "feedback_competence",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "feedback_competence",
        "competences",
        ["competence_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        None,
        "feedback_competence",
        "feedback",
        ["feedback_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "feedback_competence", type_="foreignkey")
    op.drop_constraint(None, "feedback_competence", type_="foreignkey")
    op.create_foreign_key(
        "feedback_competence_feedback_id_fkey",
        "feedback_competence",
        "feedback",
        ["feedback_id"],
        ["id"],
    )
    op.create_foreign_key(
        "feedback_competence_competence_id_fkey",
        "feedback_competence",
        "competences",
        ["competence_id"],
        ["id"],
    )
    op.drop_constraint(None, "activity_competence", type_="foreignkey")
    op.drop_constraint(None, "activity_competence", type_="foreignkey")
    op.create_foreign_key(
        "activity_competence_competence_id_fkey",
        "activity_competence",
        "competences",
        ["competence_id"],
        ["id"],
    )
    op.create_foreign_key(
        "activity_competence_activity_id_fkey",
        "activity_competence",
        "activities",
        ["activity_id"],
        ["id"],
    )
    # ### end Alembic commands ###
