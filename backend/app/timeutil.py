from datetime import UTC, datetime


def as_utc(dt: datetime) -> datetime:
    """SQLite tidak menyimpan zona waktu; anggap nilai naive sebagai UTC."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None
