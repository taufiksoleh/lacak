"""Import aktivitas dari file JSON/CSV untuk platform yang API-nya terbatas.

Format JSON: list objek, atau {"activities": [...]}. Format CSV: header dengan kolom yang sama.
Kolom: platform, handle, type, text, url, created_at (ISO 8601), targets (opsional,
dipisah ';' dengan format "handle" atau "kind:handle").
"""

import csv
import io
import json
from dataclasses import dataclass

from app.connectors.base import NormalizedActivity, extract_mentions, extract_urls
from app.timeutil import parse_iso

VALID_TYPES = {"post", "reply", "comment", "repost", "quote"}
VALID_KINDS = {"mention", "reply", "repost", "quote", "comment"}


@dataclass
class ImportedRow:
    handle: str
    activity: NormalizedActivity


def _parse_targets(raw, text: str, handle: str) -> list[dict]:
    targets: list[dict] = []
    items = raw if isinstance(raw, list) else [t for t in str(raw or "").split(";") if t.strip()]
    for item in items:
        if isinstance(item, dict):
            h, kind = str(item.get("handle", "")), str(item.get("kind", "mention"))
        else:
            kind, _, h = str(item).strip().rpartition(":")
            kind = kind or "mention"
        h = h.strip().lstrip("@").lower()
        if h and h != handle and kind in VALID_KINDS:
            targets.append({"handle": h, "kind": kind})
    known = {t["handle"] for t in targets}
    for h in extract_mentions(text):
        if h not in known and h != handle:
            targets.append({"handle": h, "kind": "mention"})
    return targets


def parse_file(filename: str, content: bytes) -> tuple[list[ImportedRow], list[str]]:
    text = content.decode("utf-8-sig")
    if filename.lower().endswith(".csv"):
        records = list(csv.DictReader(io.StringIO(text)))
    else:
        data = json.loads(text)
        records = data.get("activities", []) if isinstance(data, dict) else data
    rows: list[ImportedRow] = []
    errors: list[str] = []
    for i, r in enumerate(records, start=1):
        if not isinstance(r, dict):
            errors.append(f"baris {i}: format tidak valid")
            continue
        platform = str(r.get("platform", "")).strip().lower()
        handle = str(r.get("handle", "")).strip().lstrip("@").lower()
        kind = str(r.get("type", "post")).strip().lower()
        created = parse_iso(str(r.get("created_at", "")))
        if not platform or not handle:
            errors.append(f"baris {i}: platform/handle kosong")
            continue
        if kind not in VALID_TYPES:
            errors.append(f"baris {i}: type '{kind}' tidak dikenal")
            continue
        if created is None:
            errors.append(f"baris {i}: created_at tidak valid")
            continue
        body = str(r.get("text", "") or "")
        rows.append(
            ImportedRow(
                handle=handle,
                activity=NormalizedActivity(
                    platform=platform,
                    type=kind,
                    created_at=created,
                    text=body,
                    url=str(r.get("url", "") or ""),
                    external_id=str(r.get("id", "") or ""),
                    targets=_parse_targets(r.get("targets"), body, handle),
                    links=extract_urls(body),
                ),
            )
        )
    return rows, errors
