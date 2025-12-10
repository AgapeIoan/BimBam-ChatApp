"""Merge heads to linearize history.

Revision ID: 7f6b6d8c9f6d
Revises: 345b1a44b4ef, a5796ab061c3
Create Date: 2025-12-10 17:15:00.000000
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "7f6b6d8c9f6d"
down_revision: Union[str, Sequence[str], None] = ("345b1a44b4ef", "a5796ab061c3")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op merge to unify divergent heads."""
    pass


def downgrade() -> None:
    pass
