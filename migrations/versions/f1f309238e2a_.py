"""empty message

Revision ID: f1f309238e2a
Revises: 00558b257826
Create Date: 2019-12-14 16:28:33.803773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1f309238e2a"
down_revision = "00558b257826"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("colors_value_key", "colors", type_="unique")
    op.drop_constraint("varieties_color_id_fkey", "varieties", type_="foreignkey")
    op.drop_column("colors", "id")
    op.drop_column("varieties", "color_id")
    op.add_column(
        "varieties", sa.Column("color_value", sa.String(length=6), nullable=True)
    )
    op.create_primary_key(None, "colors", ["value"])
    op.create_foreign_key(
        None, "varieties", "colors", ["color_value"], ["value"], ondelete="CASCADE"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "varieties",
        sa.Column("color_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(None, "varieties", type_="foreignkey")
    op.create_foreign_key(
        "varieties_color_id_fkey",
        "varieties",
        "colors",
        ["color_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("varieties", "color_value")
    op.add_column(
        "colors",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('colors_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
    )
    op.create_unique_constraint("colors_value_key", "colors", ["value"])
    # ### end Alembic commands ###
