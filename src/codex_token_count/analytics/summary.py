from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from ..models import ThreadRecord


def build_summary(threads: Iterable[ThreadRecord], now: datetime | None = None) -> dict[str, object]:
    items = list(threads)
    current = now or datetime.now(timezone.utc)
    last_7_start = current - timedelta(days=7)
    last_30_start = current - timedelta(days=30)

    return {
        "total_sessions": len(items),
        "total_tokens": sum(item.tokens_used for item in items),
        "last_updated_at": max((item.updated_at for item in items), default=None),
        "tokens_last_7_days": sum(item.tokens_used for item in items if item.updated_at >= last_7_start),
        "tokens_last_30_days": sum(item.tokens_used for item in items if item.updated_at >= last_30_start),
    }
