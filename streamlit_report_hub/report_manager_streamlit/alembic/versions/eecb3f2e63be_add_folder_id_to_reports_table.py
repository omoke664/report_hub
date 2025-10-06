"""Add folder_id to reports table

Revision ID: eecb3f2e63be
Revises: 4da1171d4650
Create Date: 2025-09-29 16:36:44.810100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eecb3f2e63be'
down_revision: Union[str, Sequence[str], None] = '4da1171d4650'
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