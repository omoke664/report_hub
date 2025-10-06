"""Add folder_id to reports table

Revision ID: 80a43a5e972c
Revises: eecb3f2e63be
Create Date: 2025-09-29 16:38:07.499075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80a43a5e972c'
down_revision: Union[str, Sequence[str], None] = 'eecb3f2e63be'
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