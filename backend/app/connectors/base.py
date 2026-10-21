import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

import httpx

MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_.]{2,30})")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def extract_mentions(text: str) -> list[str]:
    seen: list[str] = []
    for m in MENTION_RE.findall(text or ""):
        handle = m.rstrip(".").lower()
        if handle and handle not in seen:
            seen.append(handle)
    return seen


def extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(u.rstrip(".,;") for u in URL_RE.findall(text or "")))


class ConnectorError(Exception):
    pass


class NotConfiguredError(ConnectorError):
    pass


@dataclass
class NormalizedProfile:
    platform: str
    handle: str
    external_id: str = ""
    display_name: str = ""
    bio: str = ""
    profile_url: str = ""
    links: list[str] = field(default_factory=list)
    followers: int | None = None
    following: int | None = None
    verified: bool = False
    created_at: datetime | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class NormalizedActivity:
    platform: str
    type: str  # post|reply|comment|repost|quote
    created_at: datetime
    text: str = ""
    url: str = ""
    external_id: str = ""
    # [{"handle": "...", "kind": "mention|reply|repost|quote"}]
    targets: list[dict] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def mention_targets(text: str, exclude: str = "") -> list[dict]:
    return [
        {"handle": h, "kind": "mention"} for h in extract_mentions(text) if h != exclude.lower()
    ]


class Connector(ABC):
    platform: str = ""
    limitations: str = ""

    def __init__(self, http: httpx.AsyncClient | None = None):
        self._http = http

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30)
        return self._http

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    async def fetch_profile(self, handle: str) -> NormalizedProfile: ...

    @abstractmethod
    async def fetch_activity(
        self, profile: NormalizedProfile, limit: int
    ) -> list[NormalizedActivity]: ...

    async def _get_json(self, url: str, **kwargs) -> dict:
        if not self.is_configured():
            raise NotConfiguredError(f"Konektor {self.platform} belum dikonfigurasi")
        try:
            resp = await self.http.get(url, **kwargs)
        except httpx.HTTPError as e:
            raise ConnectorError(f"{self.platform}: gagal menghubungi API ({e})") from e
        if resp.status_code >= 400:
            raise ConnectorError(
                f"{self.platform}: API mengembalikan {resp.status_code}: {resp.text[:300]}"
            )
        return resp.json()
