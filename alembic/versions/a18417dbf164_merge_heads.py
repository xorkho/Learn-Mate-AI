"""merge heads

Revision ID: a18417dbf164
Revises: 904897bca479, c5f3e7a17a91
Create Date: 2026-08-05 04:13:14.982481

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a18417dbf164'
down_revision: Union[str, Sequence[str], None] = ('904897bca479', 'c5f3e7a17a91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
