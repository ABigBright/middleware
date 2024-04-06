"""drop system_filesystem table

Revision ID: 334c69c59196
Revises: 058f00440129
Create Date: 2023-12-16 15:01:53.612472+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '334c69c59196'
down_revision = '058f00440129'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('system_filesystem')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('system_filesystem',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('identifier', sa.VARCHAR(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('identifier', name='uq_system_filesystem_identifier')
    )
    # ### end Alembic commands ###