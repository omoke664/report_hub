"""Add folder_id to reports table

Revision ID: f27a0d0a7d6f
Revises: 
Create Date: 2025-09-29 16:23:35.074410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f27a0d0a7d6f'
down_revision: Union[str, Sequence[str], None] = None
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