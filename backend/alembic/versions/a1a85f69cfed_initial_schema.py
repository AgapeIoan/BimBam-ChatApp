"""initial schema (merged placeholder)

Revision ID: a1a85f69cfed
Revises: 411a7da5812f
Create Date: 2025-12-03 14:37:20.195328

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'a1a85f69cfed'
down_revision: Union[str, None] = '411a7da5812f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge migration to linearize heads."""
    pass


def downgrade() -> None:
    pass
