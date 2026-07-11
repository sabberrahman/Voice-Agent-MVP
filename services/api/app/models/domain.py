from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CallDirection(StrEnum):
    inbound = "inbound"
    outbound = "outbound"


class CallStatus(StrEnum):
    queued = "queued"
    ringing = "ringing"
    active = "active"
    completed = "completed"
    failed = "failed"


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    locale: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    customers: Mapped[list["Customer"]] = relationship(back_populates="tenant")


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="customers")
    calls: Mapped[list["Call"]] = relationship(back_populates="customer")


class Agent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    stt_provider: Mapped[str | None] = mapped_column(String(64))
    llm_provider: Mapped[str | None] = mapped_column(String(64))
    tts_provider: Mapped[str | None] = mapped_column(String(64))
    prompt_template: Mapped[str | None] = mapped_column(Text)
    tools_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="draft", nullable=False)
    schedule: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Call(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "calls"
    __table_args__ = (Index("ix_calls_tenant_status_created", "tenant_id", "status", "created_at"),)

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("customers.id"))
    agent_id: Mapped[UUID | None] = mapped_column(ForeignKey("agents.id"))
    campaign_id: Mapped[UUID | None] = mapped_column(ForeignKey("campaigns.id"))
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=CallStatus.queued, nullable=False)
    from_number: Mapped[str | None] = mapped_column(String(64))
    to_number: Mapped[str | None] = mapped_column(String(64))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    customer: Mapped[Customer | None] = relationship(back_populates="calls")
    sessions: Mapped[list["CallSession"]] = relationship(back_populates="call")


class CallSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "call_sessions"

    call_id: Mapped[UUID] = mapped_column(ForeignKey("calls.id"), nullable=False)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    provider_session_id: Mapped[str | None] = mapped_column(String(255))
    telephony_provider: Mapped[str] = mapped_column(String(64), default="freeswitch", nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="starting", nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    call: Mapped[Call] = relationship(back_populates="sessions")


class CallEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "call_events"
    __table_args__ = (Index("ix_call_events_call_created", "call_id", "created_at"),)

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    call_id: Mapped[UUID] = mapped_column(ForeignKey("calls.id"), nullable=False)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("call_sessions.id"))
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Transcript(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transcripts"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    call_id: Mapped[UUID] = mapped_column(ForeignKey("calls.id"), nullable=False)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("call_sessions.id"))
    speaker: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[int | None] = mapped_column(Integer)


class Summary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "summaries"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    call_id: Mapped[UUID] = mapped_column(ForeignKey("calls.id"), nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="bn-BD", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_items: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Recording(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recordings"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    call_id: Mapped[UUID] = mapped_column(ForeignKey("calls.id"), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(64), default="local", nullable=False)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="audio/wav", nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)


class ConversationMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversation_memory"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("customers.id"))
    call_id: Mapped[UUID | None] = mapped_column(ForeignKey("calls.id"))
    memory_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[UUID | None] = mapped_column(ForeignKey("tenants.id"))
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"

    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
