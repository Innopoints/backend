"""empty message

Revision ID: 4024ea77b26e
Revises: 
Create Date: 2019-11-17 20:48:51.191056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4024ea77b26e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accounts',
    sa.Column('full_name', sa.String(length=256), nullable=False),
    sa.Column('university_status', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=128), nullable=False),
    sa.Column('telegram_username', sa.String(length=32), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('email')
    )
    op.create_table('colors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(length=6), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('competences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('type', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=1024), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('addition_time', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('static_files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mimetype', sa.String(length=255), nullable=False),
    sa.Column('namespace', sa.String(length=64), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('projects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('image_id', sa.Integer(), nullable=True),
    sa.Column('creation_time', sa.DateTime(), nullable=True),
    sa.Column('organizer', sa.String(length=128), nullable=True),
    sa.Column('creator_email', sa.String(length=128), nullable=False),
    sa.Column('admin_feedback', sa.String(length=1024), nullable=True),
    sa.Column('review_status', sa.Enum('pending', 'approved', 'rejected', name='reviewstatus'), nullable=True),
    sa.Column('lifetime_stage', sa.Enum('draft', 'ongoing', 'past', name='lifetimestage'), nullable=False),
    sa.ForeignKeyConstraint(['creator_email'], ['accounts.email'], ),
    sa.ForeignKeyConstraint(['image_id'], ['static_files.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('varieties',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('size', sa.String(length=3), nullable=True),
    sa.Column('color_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['color_id'], ['colors.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=1024), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('working_hours', sa.Integer(), nullable=True),
    sa.Column('reward_rate', sa.Integer(), nullable=True),
    sa.Column('fixed_reward', sa.Boolean(), nullable=False),
    sa.Column('people_required', sa.Integer(), nullable=False),
    sa.Column('telegram_required', sa.Boolean(), nullable=False),
    sa.Column('application_deadline', sa.DateTime(), nullable=True),
    sa.Column('feedback_questions', sa.ARRAY(sa.String(length=1024)), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product_images',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('variety_id', sa.Integer(), nullable=False),
    sa.Column('image_id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['image_id'], ['static_files.id'], ),
    sa.ForeignKeyConstraint(['variety_id'], ['varieties.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('project_files',
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['static_files.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('project_id', 'file_id')
    )
    op.create_table('project_moderation',
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('account_email', sa.String(length=128), nullable=False),
    sa.ForeignKeyConstraint(['account_email'], ['accounts.email'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('project_id', 'account_email')
    )
    op.create_table('stock_changes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.Column('status', sa.Enum('carried_out', 'pending', 'ready_for_pickup', 'rejected', name='stockchangestatus'), nullable=False),
    sa.Column('account_email', sa.String(length=128), nullable=False),
    sa.Column('variety_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['account_email'], ['accounts.email'], ),
    sa.ForeignKeyConstraint(['variety_id'], ['varieties.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('activity_competence',
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('competence_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
    sa.ForeignKeyConstraint(['competence_id'], ['competences.id'], ),
    sa.PrimaryKeyConstraint('activity_id', 'competence_id')
    )
    op.create_table('applications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('applicant_email', sa.String(length=128), nullable=False),
    sa.Column('activity_id', sa.Integer(), nullable=False),
    sa.Column('comment', sa.String(length=1024), nullable=False),
    sa.Column('application_time', sa.DateTime(), nullable=False),
    sa.Column('telegram_username', sa.String(length=32), nullable=False),
    sa.Column('status', sa.Enum('approved', 'pending', 'rejected', name='applicationstatus'), nullable=False),
    sa.Column('actual_hours', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
    sa.ForeignKeyConstraint(['applicant_email'], ['accounts.email'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recipient_email', sa.String(length=128), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=True),
    sa.Column('project_id', sa.Integer(), nullable=True),
    sa.Column('activity_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('purchase_ready', 'new_arrivals', 'claim_ipts', 'apl_accept', 'apl_reject', 'service', 'act_table_reject', 'all_feedback_in', 'out_of_stock', 'new_purchase', 'proj_final_review', name='notificationtype'), nullable=False),
    sa.CheckConstraint('(product_id IS NULL)::INTEGER + (project_id IS NULL)::INTEGER + (activity_id IS NULL)::INTEGER < 1', name='not more than 1 related object'),
    sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.ForeignKeyConstraint(['recipient_email'], ['accounts.email'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('application_id', sa.Integer(), nullable=False),
    sa.Column('answers', sa.ARRAY(sa.String(length=1024)), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('application_id', sa.Integer(), nullable=False),
    sa.Column('rating', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=1024), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feedback_competence',
    sa.Column('feedback_id', sa.Integer(), nullable=False),
    sa.Column('competence_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['competence_id'], ['competences.id'], ),
    sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ),
    sa.PrimaryKeyConstraint('feedback_id', 'competence_id')
    )
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_email', sa.String(length=128), nullable=False),
    sa.Column('change', sa.Integer(), nullable=False),
    sa.Column('stock_change_id', sa.Integer(), nullable=True),
    sa.Column('feedback_id', sa.Integer(), nullable=True),
    sa.CheckConstraint('(stock_change_id IS NULL) != (feedback_id IS NULL)', name='feedback xor stock_change'),
    sa.ForeignKeyConstraint(['account_email'], ['accounts.email'], ),
    sa.ForeignKeyConstraint(['feedback_id'], ['feedback.id'], ),
    sa.ForeignKeyConstraint(['stock_change_id'], ['stock_changes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('feedback_competence')
    op.drop_table('reports')
    op.drop_table('feedback')
    op.drop_table('notifications')
    op.drop_table('applications')
    op.drop_table('activity_competence')
    op.drop_table('stock_changes')
    op.drop_table('project_moderation')
    op.drop_table('project_files')
    op.drop_table('product_images')
    op.drop_table('activities')
    op.drop_table('varieties')
    op.drop_table('projects')
    op.drop_table('static_files')
    op.drop_table('products')
    op.drop_table('competences')
    op.drop_table('colors')
    op.drop_table('accounts')
    # ### end Alembic commands ###
