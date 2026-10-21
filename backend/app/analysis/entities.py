"""Deteksi indikasi afiliasi berbasis aturan. Hasilnya indikasi + bukti, bukan kesimpulan."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import yaml

SEED_FILE = Path(__file__).resolve().parents[2] / "data" / "entities.yaml"

# Bobot per jenis bukti, dan batas atas total per jenis
WEIGHTS = {
    "profile_link": (0.5, 0.6),
    "bio": (0.4, 0.5),
    "repost": (0.05, 0.3),
    "quote": (0.05, 0.3),
    "reply": (0.04, 0.3),
    "mention": (0.04, 0.3),
    "comment": (0.04, 0.3),
    "post_link": (0.04, 0.2),
    "keyword": (0.02, 0.1),
}
# Tanpa bukti dari profil (tautan/bio), interaksi publik saja tidak boleh dinilai "kuat"
INTERACTION_ONLY_CAP = 0.45
PROFILE_KINDS = {"profile_link", "bio"}
GENERIC_SUFFIXES = {
    ".go.id": ("Instansi pemerintah (domain .go.id)", "government"),
    ".mil.id": ("Institusi militer (domain .mil.id)", "government"),
}


@dataclass
class EntityDef:
    name: str
    category: str
    handles: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class AccountData:
    platform: str
    handle: str
    bio: str
    links: list[str]
    profile_url: str


@dataclass
class ActivityData:
    platform: str
    type: str
    text: str
    url: str
    targets: list[dict]
    links: list[str]


def load_seed() -> list[dict]:
    with SEED_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f).get("entities", [])


def domain_of(url: str) -> str:
    host = urlparse(url if "://" in url else "https://" + url).hostname or ""
    return host.lower().removeprefix("www.")


def domain_matches(host: str, domain: str) -> bool:
    domain = domain.lower()
    return host == domain or host.endswith("." + domain)


def _keyword_re(keywords: list[str]) -> re.Pattern | None:
    kws = [re.escape(k) for k in keywords if k.strip()]
    if not kws:
        return None
    return re.compile(r"(?<!\w)(" + "|".join(kws) + r")(?!\w)", re.IGNORECASE)


def _confidence(scores: dict[str, float]) -> float:
    p = 1.0
    for s in scores.values():
        p *= 1 - s
    combined = 1 - p
    if not PROFILE_KINDS & scores.keys():
        combined = min(combined, INTERACTION_ONLY_CAP)
    return round(combined, 3)


class _Scorer:
    def __init__(self) -> None:
        self.raw: dict[str, float] = {}
        self.evidence: list[dict] = []

    def add(self, kind: str, detail: str, url: str = "") -> None:
        step, cap = WEIGHTS[kind]
        self.raw[kind] = min(cap, self.raw.get(kind, 0) + step)
        if len(self.evidence) < 25:
            self.evidence.append({"type": kind, "detail": detail, "url": url})


def _host_matcher(ent: EntityDef, entities: list[EntityDef]):
    suffix = next((s for s, (n, _) in GENERIC_SUFFIXES.items() if n == ent.name), None)
    specific = [d for e in entities for d in e.domains]

    def hit(url: str) -> bool:
        host = domain_of(url)
        if suffix:
            # Domain generik hanya dipakai bila tidak cocok dengan entitas spesifik
            return host.endswith(suffix) and not any(domain_matches(host, d) for d in specific)
        return any(domain_matches(host, d) for d in ent.domains)

    return hit


def _score(
    ent: EntityDef,
    entities: list[EntityDef],
    accounts: list[AccountData],
    activities: list[ActivityData],
) -> _Scorer:
    handles = {h.lower().lstrip("@") for h in ent.handles}
    kw_re = _keyword_re(ent.keywords)
    host_hit = _host_matcher(ent, entities)
    sc = _Scorer()

    for acc in accounts:
        for link in acc.links:
            if host_hit(link):
                sc.add("profile_link", f"Tautan di profil {acc.platform} @{acc.handle}", link)
        bio_mentions = {m.lower() for m in re.findall(r"@([\w.]+)", acc.bio)}
        if (handles & bio_mentions) or (kw_re and kw_re.search(acc.bio)):
            sc.add("bio", f"Bio {acc.platform} @{acc.handle}: “{acc.bio[:160]}”", acc.profile_url)

    for act in activities:
        for t in act.targets:
            if t.get("handle", "").lower() in handles:
                kind = t.get("kind", "mention")
                kind = kind if kind in WEIGHTS else "mention"
                detail = f"{kind} @{t['handle']} di {act.platform}: “{act.text[:140]}”"
                sc.add(kind, detail, act.url)
        for link in act.links:
            if host_hit(link):
                sc.add("post_link", f"Membagikan tautan {domain_of(link)}", act.url or link)
        if kw_re and (m := kw_re.search(act.text)):
            sc.add("keyword", f"Menyebut “{m.group(0)}”: “{act.text[:140]}”", act.url)
    return sc


def match_entities(
    entities: list[EntityDef], accounts: list[AccountData], activities: list[ActivityData]
) -> list[dict]:
    generic = [EntityDef(name=name, category=cat) for name, cat in GENERIC_SUFFIXES.values()]
    results: list[dict] = []
    for ent in [*entities, *generic]:
        sc = _score(ent, entities, accounts, activities)
        if not sc.raw:
            continue
        results.append(
            {
                "entity_name": ent.name,
                "category": ent.category,
                "confidence": _confidence(sc.raw),
                "method": "rule",
                "rationale": _rationale(sc.raw),
                "evidence": sc.evidence,
            }
        )
    return sorted(results, key=lambda r: r["confidence"], reverse=True)


LABELS = {
    "profile_link": "tautan resmi di profil",
    "bio": "disebut di bio",
    "repost": "repost",
    "quote": "quote",
    "reply": "membalas",
    "mention": "mention",
    "comment": "komentar",
    "post_link": "membagikan tautan domain resmi",
    "keyword": "menyebut nama",
}


def _rationale(raw: dict[str, float]) -> str:
    parts = [LABELS[k] for k, _ in sorted(raw.items(), key=lambda kv: -kv[1])]
    note = ""
    if not PROFILE_KINDS & raw.keys():
        note = " Hanya berdasar interaksi publik — belum tentu afiliasi formal."
    return "Indikator: " + ", ".join(parts) + "." + note
