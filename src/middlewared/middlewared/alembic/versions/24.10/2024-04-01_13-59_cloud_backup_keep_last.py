"""Cloud backup keep last

Revision ID: 1a6fc6735dc2
Revises: 7836261b2f64
Create Date: 2024-04-01 13:59:15.352191+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a6fc6735dc2'
down_revision = '7836261b2f64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tasks_cloud_backup', schema=None) as batch_op:
        batch_op.add_column(sa.Column('keep_last', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tasks_cloud_backup', schema=None) as batch_op:
        batch_op.drop_column('keep_last')

    # ### end Alembic commands ###
