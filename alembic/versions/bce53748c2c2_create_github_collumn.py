"""create_github_collumn

Revision ID: bce53748c2c2
Revises: b50a065f412c
Create Date: 2023-07-28 14:39:42.918635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bce53748c2c2'
down_revision = 'b50a065f412c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('version', sa.Column('stars', sa.Integer))
    op.add_column('version', sa.Column('forks', sa.Integer))
    op.add_column('version', sa.Column('subscribers', sa.Integer))


def downgrade() -> None:
    pass
