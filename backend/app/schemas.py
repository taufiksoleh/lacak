from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Platform = Literal["instagram", "threads", "x", "youtube"]
EntityCategory = Literal["government", "party", "company", "ngo", "media", "other"]


class AccountIn(BaseModel):
    platform: Platform
    handle: str = Field(min_length=1, max_length=100)

    @field_validator("handle")
    @classmethod
    def strip_handle(cls, v: str) -> str:
        v = v.strip().lstrip("@").strip()
        if not v:
            raise ValueError("handle kosong")
        return v


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject_name: str = Field(default="", max_length=200)
    purpose: str = Field(
        min_length=20,
        description="Tujuan investigasi wajib diisi (min. 20 karakter) untuk akuntabilitas.",
    )
    accounts: list[AccountIn] = Field(min_length=1, max_length=12)
    demo: bool = False


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    handle: str
    external_id: str
    display_name: str
    bio: str
    profile_url: str
    links: list
    followers: int | None
    following: int | None
    verified: bool
    created_at_platform: datetime | None
    error: str
    activity_count: int = 0


class InvestigationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    subject_name: str
    purpose: str
    demo: bool
    status: str
    status_detail: str
    created_at: datetime
    collected_at: datetime | None


class InvestigationOut(InvestigationSummary):
    accounts: list[AccountOut]
    analysis: dict


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    handle: str = ""
    type: str
    text: str
    url: str
    created_at: datetime
    targets: list
    links: list
    metrics: dict
    source: str


class TimelinePage(BaseModel):
    total: int
    items: list[ActivityOut]


class EntityIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    category: EntityCategory
    handles: list[str] = []
    domains: list[str] = []
    keywords: list[str] = []


class EntityOut(EntityIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_name: str
    category: str
    confidence: float
    method: str
    rationale: str
    evidence: list


class WebFindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    snippet: str


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    investigation_id: int | None
    action: str
    detail: str
    created_at: datetime


class ConnectorStatus(BaseModel):
    platform: str
    configured: bool
    limitations: str


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
