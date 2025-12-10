"""add message edited_at and reactions

Revision ID: 345b1a44b4ef
Revises: 411a7da5812f
Create Date: 2025-12-10 11:39:32.559806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '345b1a44b4ef'
down_revision: Union[str, Sequence[str], None] = '411a7da5812f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add edited fields to messages
    op.add_column(
        "messages",
        sa.Column("edited_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.add_column(
        "messages",
        sa.Column("edited_by_id", sa.UUID(), nullable=True),
    )
    # create foreign key from messages.edited_by_id -> users.id
    op.create_foreign_key(
        "fk_messages_edited_by_id_users",
        "messages",
        "users",
        ["edited_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create message_edits table
    op.create_table(
        "message_edits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("editor_id", sa.UUID(), nullable=True),
        sa.Column("old_content", sa.Text(), nullable=False),
        sa.Column("new_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["editor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_edits_message_id", "message_edits", ["message_id"], unique=False)

    # Create message_reactions table
    op.create_table(
        "message_reactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("emoji", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_reaction_once"),
    )
    op.create_index("ix_message_reactions_message_id", "message_reactions", ["message_id"], unique=False)
    op.create_index("ix_message_reactions_user_id", "message_reactions", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop reactions table and indexes
    op.drop_index("ix_message_reactions_user_id", table_name="message_reactions")
    op.drop_index("ix_message_reactions_message_id", table_name="message_reactions")
    op.drop_table("message_reactions")

    # Drop edits table and index
    op.drop_index("ix_message_edits_message_id", table_name="message_edits")
    op.drop_table("message_edits")

    # Drop foreign key and columns from messages
    op.drop_constraint("fk_messages_edited_by_id_users", "messages", type_="foreignkey")
    op.drop_column("messages", "edited_by_id")
    op.drop_column("messages", "edited_at")
