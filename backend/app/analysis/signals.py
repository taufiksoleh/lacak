"""Indikator perilaku (mis. pola akun terkoordinasi/"buzzer"). Hanya indikator, bukan label."""

import math
import re
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from app.timeutil import as_utc


def _norm(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text.lower())
    text = re.sub(r"^rt @\w+:?", "", text)
    return re.sub(r"\W+", " ", text).strip()


def _level(value: float, medium: float, high: float) -> str:
    return "high" if value >= high else "medium" if value >= medium else "low"


def behavior_signals(
    items: list[tuple[str, str, datetime]],
    account_created: list[datetime],
    tz: str,
) -> dict:
    """items: (type, text, created_at)."""
    n = len(items)
    if n < 5:
        return {"indicators": [], "overall": "insufficient", "note": "Data terlalu sedikit (< 5)."}
    zone = ZoneInfo(tz)
    local = [as_utc(c).astimezone(zone) for _, _, c in items]
    indicators = []

    reposts = sum(1 for t, _, _ in items if t == "repost")
    ratio = reposts / n
    indicators.append(
        {
            "key": "repost_ratio",
            "label": "Rasio repost",
            "value": round(ratio, 2),
            "display": f"{ratio:.0%}",
            "level": _level(ratio, 0.4, 0.7),
            "description": "Porsi aktivitas yang hanya menyebarkan ulang konten orang lain.",
        }
    )

    texts = [_norm(x) for t, x, _ in items if t != "repost" and len(_norm(x)) > 15]
    dup_ratio = 0.0
    if texts:
        counts = Counter(texts)
        dup_ratio = sum(c for c in counts.values() if c > 1) / len(texts)
    indicators.append(
        {
            "key": "duplicate_text",
            "label": "Teks berulang",
            "value": round(dup_ratio, 2),
            "display": f"{dup_ratio:.0%}",
            "level": _level(dup_ratio, 0.3, 0.6),
            "description": "Porsi postingan/balasan dengan teks yang sama persis (copy-paste).",
        }
    )

    hours = Counter(t.hour for t in local)
    entropy = -sum((c / n) * math.log2(c / n) for c in hours.values())
    regularity = 1 - entropy / math.log2(24)
    indicators.append(
        {
            "key": "hour_concentration",
            "label": "Konsentrasi jam posting",
            "value": round(regularity, 2),
            "display": f"{regularity:.2f}",
            "level": _level(regularity, 0.45, 0.65),
            "description": "Semakin tinggi, semakin terpusat di jam tertentu "
            "(bisa jadwal otomatis).",
        }
    )

    night = sum(1 for t in local if 0 <= t.hour < 5) / n
    indicators.append(
        {
            "key": "night_activity",
            "label": "Aktivitas dini hari (00–05)",
            "value": round(night, 2),
            "display": f"{night:.0%}",
            "level": _level(night, 0.25, 0.5),
            "description": "Porsi aktivitas pada jam 00.00–05.00 waktu lokal.",
        }
    )

    per_day = Counter(t.date() for t in local)
    peak = max(per_day.values())
    indicators.append(
        {
            "key": "burst",
            "label": "Puncak aktivitas harian",
            "value": peak,
            "display": f"{peak} aktivitas/hari",
            "level": _level(peak, 30, 80),
            "description": "Jumlah aktivitas terbanyak dalam satu hari.",
        }
    )

    if account_created:
        oldest = min(as_utc(c) for c in account_created)
        newest_activity = max(as_utc(c) for _, _, c in items)
        age = max(1, (newest_activity - oldest).days)
        rate = n / age
        indicators.append(
            {
                "key": "young_high_volume",
                "label": "Volume vs umur akun",
                "value": round(rate, 2),
                "display": f"{rate:.1f}/hari selama {age} hari",
                "level": "high"
                if age < 90 and rate > 20
                else "medium"
                if age < 180 and rate > 10
                else "low",
                "description": "Akun baru dengan volume sangat tinggi patut dicermati.",
            }
        )

    score = {"low": 0, "medium": 1, "high": 2}
    total = sum(score[i["level"]] for i in indicators)
    overall = "high" if total >= 6 else "medium" if total >= 3 else "low"
    return {
        "indicators": indicators,
        "overall": overall,
        "note": "Indikator statistik; perlu verifikasi manusia sebelum menarik kesimpulan.",
    }
