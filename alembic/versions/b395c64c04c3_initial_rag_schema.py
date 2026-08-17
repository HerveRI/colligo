"""initial rag schema

Revision ID: 0001_initial
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "rag"
RO_ROLE = "colligo_ro"
EMBED_DIM = 768


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        f"""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{RO_ROLE}') THEN
            CREATE ROLE {RO_ROLE} NOLOGIN;
          END IF;
        END $$;
        """
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_documents"),
        sa.UniqueConstraint("source", name="uq_documents_source"),
        schema=SCHEMA,
    )

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(EMBED_DIM), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(32), server_default="document", nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chunks"),
        sa.ForeignKeyConstraint(
            ["document_id"],
            [f"{SCHEMA}.documents.id"],
            name="fk_chunks_document_id_documents",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("document_id", "position", name="uq_chunks_document_id"),
        sa.CheckConstraint(
            "source_type IN ('document', 'crm')", name="ck_chunks_source_type_valid"
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"], schema=SCHEMA)
    op.create_index("ix_chunks_source_type", "chunks", ["source_type"], schema=SCHEMA)

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_conversations"),
        schema=SCHEMA,
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            [f"{SCHEMA}.conversations.id"],
            name="fk_messages_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("conversation_id", "position", name="uq_messages_conversation_id"),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')", name="ck_messages_role_valid"
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], schema=SCHEMA)

    op.create_table(
        "tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String(64), nullable=False),
        sa.Column("arguments", postgresql.JSONB(), nullable=False),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("ok", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("iteration", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tool_calls"),
        sa.ForeignKeyConstraint(
            ["message_id"],
            [f"{SCHEMA}.messages.id"],
            name="fk_tool_calls_message_id_messages",
            ondelete="CASCADE",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_tool_calls_message_id", "tool_calls", ["message_id"], schema=SCHEMA)

    op.execute(f"GRANT USAGE ON SCHEMA {SCHEMA} TO {RO_ROLE}")
    op.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {SCHEMA} TO {RO_ROLE}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {SCHEMA} GRANT SELECT ON TABLES TO {RO_ROLE}")


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE")
