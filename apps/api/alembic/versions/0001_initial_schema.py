# In apps/api/alembic/versions/0001_initial_schema.py

"""Initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # NOTE: The explicit CREATE TYPE statements have been removed.
    # SQLAlchemy's create_table operation will handle the creation of ENUM types automatically
    # based on the model definitions.

    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("user", "admin", name="user_role", create_type=True), # Changed create_type to True
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "email IS NOT NULL OR phone_number IS NOT NULL", name="email_or_phone_check"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone_number"),
    )

    # Create content table
    op.create_table(
        "content",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "source_type",
            postgresql.ENUM("pdf", "youtube", name="content_type", create_type=True), # Changed create_type to True
            nullable=False,
        ),
        sa.Column(
            "language",
            postgresql.ENUM("en", "ta", name="language_code", create_type=True), # Changed create_type to True
            nullable=False,
        ),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column(
            "needs_translation", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending", "processing", "completed", "failed", name="content_status", create_type=True # Changed create_type to True
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "sender",
            postgresql.ENUM("user", "ai", name="message_sender", create_type=True), # Changed create_type to True
            nullable=False,
        ),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("video_timestamp_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_conversations_user_id", "conversations", ["user_id"])
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("idx_content_category", "content", ["category"])
    op.create_index("idx_content_language", "content", ["language"])

    # Create update timestamp triggers
    op.execute(
        """
        CREATE OR REPLACE FUNCTION trigger_set_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = NOW();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        "CREATE TRIGGER set_timestamp_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();"
    )
    op.execute(
        "CREATE TRIGGER set_timestamp_content BEFORE UPDATE ON content FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();"
    )
    op.execute(
        "CREATE TRIGGER set_timestamp_conversations BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE PROCEDURE trigger_set_timestamp();"
    )


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS set_timestamp_conversations ON conversations;")
    op.execute("DROP TRIGGER IF EXISTS set_timestamp_content ON content;")
    op.execute("DROP TRIGGER IF EXISTS set_timestamp_users ON users;")
    op.execute("DROP FUNCTION IF EXISTS trigger_set_timestamp();")

    # Drop indexes
    op.drop_index("idx_content_language", table_name="content")
    op.drop_index("idx_content_category", table_name="content")
    op.drop_index("idx_messages_conversation_id", table_name="messages")
    op.drop_index("idx_conversations_user_id", table_name="conversations")

    # Drop tables
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("content")
    op.drop_table("users")

    # Drop enum types - This is now essential in the downgrade
    op.execute("DROP TYPE message_sender")
    op.execute("DROP TYPE language_code")
    op.execute("DROP TYPE content_status")
    op.execute("DROP TYPE content_type")
    op.execute("DROP TYPE user_role")