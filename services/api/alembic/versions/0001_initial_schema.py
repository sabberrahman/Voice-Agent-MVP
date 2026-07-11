"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-11 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    for table, cols in {
        "customers": [
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("external_id", sa.String(length=255), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("phone_number", sa.String(length=64), nullable=True),
            sa.Column("language", sa.String(length=32), nullable=False),
            sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        ],
        "agents": [
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("language", sa.String(length=32), nullable=False),
            sa.Column("stt_provider", sa.String(length=64), nullable=True),
            sa.Column("llm_provider", sa.String(length=64), nullable=True),
            sa.Column("tts_provider", sa.String(length=64), nullable=True),
            sa.Column("prompt_template", sa.Text(), nullable=True),
            sa.Column("tools_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
        ],
        "campaigns": [
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=64), nullable=False),
            sa.Column("schedule", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        ],
        "api_keys": [
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("key_hash", sa.String(length=255), nullable=False),
            sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        ],
    }.items():
        op.create_table(
            table,
            *cols,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    op.create_table(
        "calls",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("from_number", sa.String(length=64), nullable=True),
        sa.Column("to_number", sa.String(length=64), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_calls_tenant_status_created", "calls", ["tenant_id", "status", "created_at"])

    op.create_table(
        "call_sessions",
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_session_id", sa.String(length=255), nullable=True),
        sa.Column("telephony_provider", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    child_tables = {
        "call_events": [
            sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        ],
        "transcripts": [
            sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("speaker", sa.String(length=64), nullable=False),
            sa.Column("language", sa.String(length=32), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("confidence", sa.Integer(), nullable=True),
        ],
        "summaries": [
            sa.Column("language", sa.String(length=32), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        ],
        "recordings": [
            sa.Column("storage_provider", sa.String(length=64), nullable=False),
            sa.Column("path", sa.String(length=1024), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=False),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
        ],
    }
    for table, cols in child_tables.items():
        op.create_table(
            table,
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
            *cols,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    op.create_index("ix_call_events_call_created", "call_events", ["call_id", "created_at"])

    op.create_table(
        "conversation_memory",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "conversation_memory",
        "recordings",
        "summaries",
        "transcripts",
        "call_events",
        "call_sessions",
        "calls",
        "api_keys",
        "campaigns",
        "agents",
        "customers",
        "tenants",
    ]:
        op.drop_table(table)
