"""Add folder_id to reports table

Revision ID: 4da1171d4650
Revises: f27a0d0a7d6f
Create Date: 2025-09-29 16:32:41.972402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4da1171d4650'
down_revision: Union[str, Sequence[str], None] = 'f27a0d0a7d6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

def upgrade():
    op.add_column('reports', sa.Column('folder_id', sa.String(), sa.ForeignKey('folders.id'), nullable=True))

def downgrade():
    op.drop_column('reports', 'folder_id')