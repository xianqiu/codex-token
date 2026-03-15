from __future__ import annotations

from collections.abc import Iterable

from ..models import ThreadRecord


def summarize_projects(threads: Iterable[ThreadRecord]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for item in threads:
        project = grouped.setdefault(
            item.cwd,
            {
                "cwd": item.cwd,
                "sessions": 0,
                "tokens_used": 0,
                "last_updated_at": item.updated_at,
            },
        )
        project["sessions"] += 1
        project["tokens_used"] += item.tokens_used
        if item.updated_at > project["last_updated_at"]:
            project["last_updated_at"] = item.updated_at

    return sorted(
        grouped.values(),
        key=lambda item: (int(item["tokens_used"]), item["last_updated_at"]),
        reverse=True,
    )
