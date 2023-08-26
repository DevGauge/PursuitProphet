"""Added nullable to user_id in goal table

Revision ID: 84cbdd0c22cc
Revises: 
Create Date: 2023-06-19 09:01:15.980098

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '84cbdd0c22cc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    table_name='log_2023_06_11'
    inspector = inspect(bind=op.get_bind())
    if table_name in inspector.get_table_names():
        op.drop_table(table_name)
    with op.batch_alter_table('goal', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=255), nullable=True))
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('goal', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('user_id')

    op.create_table('log_2023_06_11',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('level', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('message', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('timestamp', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='log_2023_06_11_pkey')
    )
    # ### end Alembic commands ###
