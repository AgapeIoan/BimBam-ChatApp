"""initial schema

Revision ID: a5796ab061c3
Revises: a1a85f69cfed
Create Date: 2025-12-03 14:56:05.331739

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'a5796ab061c3'
down_revision: Union[str, None] = 'a1a85f69cfed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
