from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from app.timeutil import as_utc

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def activity_stats(items: list[tuple[str, str, datetime]], tz: str) -> dict:
    """items: (platform, type, created_at). Hasil dihitung pada zona waktu `tz`."""
    zone = ZoneInfo(tz)
    heatmap = [[0] * 24 for _ in range(7)]
    by_type: Counter[str] = Counter()
    by_platform: Counter[str] = Counter()
    daily: Counter[str] = Counter()
    local_times = []
    for platform, kind, created in items:
        local = as_utc(created).astimezone(zone)
        local_times.append(local)
        heatmap[local.weekday()][local.hour] += 1
        by_type[kind] += 1
        by_platform[platform] += 1
        daily[local.date().isoformat()] += 1

    total = len(items)
    if not total:
        return {"total": 0, "timezone": tz, "heatmap": heatmap, "days": DAYS}

    hours = Counter(t.hour for t in local_times)
    weekdays = Counter(t.weekday() for t in local_times)
    first, last = min(local_times), max(local_times)
    span_days = max(1, (last.date() - first.date()).days + 1)
    return {
        "total": total,
        "timezone": tz,
        "first": first.isoformat(),
        "last": last.isoformat(),
        "span_days": span_days,
        "avg_per_day": round(total / span_days, 2),
        "active_days": len(daily),
        "by_type": dict(by_type.most_common()),
        "by_platform": dict(by_platform.most_common()),
        "by_hour": [hours.get(h, 0) for h in range(24)],
        "most_active_hour": hours.most_common(1)[0][0],
        "most_active_day": DAYS[weekdays.most_common(1)[0][0]],
        "daily": [{"date": d, "count": c} for d, c in sorted(daily.items())],
        "heatmap": heatmap,
        "days": DAYS,
    }
