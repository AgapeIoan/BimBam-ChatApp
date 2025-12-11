"""Ensure messages table uses utf8mb4 for emoji support.

Revision ID: 8f0c9b1d6b0d
Revises: 7f6b6d8c9f6d
Create Date: 2025-12-12 12:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "8f0c9b1d6b0d"
down_revision = "7f6b6d8c9f6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind and bind.dialect.name.startswith("mysql"):
        # Convert the entire table to utf8mb4 to retain emojis
        op.execute("ALTER TABLE messages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")


def downgrade() -> None:
    bind = op.get_bind()
    if bind and bind.dialect.name.startswith("mysql"):
        # Revert to utf8 if needed (may truncate 4-byte chars)
        op.execute("ALTER TABLE messages CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;")
