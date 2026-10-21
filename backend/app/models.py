from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    subject_name: Mapped[str] = mapped_column(String(200), default="")
    purpose: Mapped[str] = mapped_column(Text)
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="new")  # new|running|done|error
    status_detail: Mapped[str] = mapped_column(Text, default="")
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    findings: Mapped[list["AffiliationFinding"]] = relationship(cascade="all, delete-orphan")
    web_findings: Mapped[list["WebFinding"]] = relationship(cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"))
    platform: Mapped[str] = mapped_column(String(20))
    handle: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(100), default="")
    display_name: Mapped[str] = mapped_column(String(200), default="")
    bio: Mapped[str] = mapped_column(Text, default="")
    profile_url: Mapped[str] = mapped_column(String(500), default="")
    links: Mapped[list] = mapped_column(JSON, default=list)
    followers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    following: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at_platform: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error: Mapped[str] = mapped_column(Text, default="")
    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    investigation: Mapped[Investigation] = relationship(back_populates="accounts")
    activities: Mapped[list["Activity"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    type: Mapped[str] = mapped_column(String(20))  # post|reply|comment|repost|quote
    external_id: Mapped[str] = mapped_column(String(100), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    # [{"handle": "kemkomdigi", "kind": "mention|reply|repost|quote"}]
    targets: Mapped[list] = mapped_column(JSON, default=list)
    links: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(20), default="api")  # api|import|demo

    account: Mapped[Account] = relationship(back_populates="activities")


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(30))  # government|party|company|ngo|media
    handles: Mapped[list] = mapped_column(JSON, default=list)
    domains: Mapped[list] = mapped_column(JSON, default=list)
    keywords: Mapped[list] = mapped_column(JSON, default=list)


class AffiliationFinding(Base):
    __tablename__ = "affiliation_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    entity_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(30))
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(10))  # rule|ai
    rationale: Mapped[str] = mapped_column(Text, default="")
    # [{"type": "...", "detail": "...", "url": "..."}]
    evidence: Mapped[list] = mapped_column(JSON, default=list)


class WebFinding(Base):
    __tablename__ = "web_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(ForeignKey("investigations.id"), index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    url: Mapped[str] = mapped_column(String(1000))
    snippet: Mapped[str] = mapped_column(Text, default="")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
