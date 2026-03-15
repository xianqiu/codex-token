from __future__ import annotations

from collections.abc import Iterable

from ..models import ThreadRecord


def top_sessions(threads: Iterable[ThreadRecord], limit: int = 10) -> list[ThreadRecord]:
    items = sorted(threads, key=lambda item: (item.tokens_used, item.updated_at), reverse=True)
    return items[:limit]
