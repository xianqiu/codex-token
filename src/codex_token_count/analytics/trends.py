from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone

from ..models import ThreadRecord, TokenEvent


def build_daily_trend(
    threads: Iterable[ThreadRecord],
    token_events: Iterable[TokenEvent],
    days: int,
    now: datetime | None = None,
) -> list[dict[str, object]]:
    current = now or datetime.now(timezone.utc)
    start_day = (current - timedelta(days=days - 1)).date()
    day_map: dict[date, int] = defaultdict(int)

    events = list(token_events)
    if events:
        previous_totals: dict[str, int] = {}
        for event in sorted(events, key=lambda item: (item.timestamp, item.session_id)):
            event_day = event.timestamp.date()
            if event_day < start_day:
                previous_totals[event.session_id] = event.total_tokens
                continue

            previous = previous_totals.get(event.session_id, 0)
            delta = max(event.total_tokens - previous, 0)
            day_map[event_day] += delta
            previous_totals[event.session_id] = event.total_tokens
    else:
        for thread in threads:
            thread_day = thread.updated_at.date()
            if thread_day >= start_day:
                day_map[thread_day] += thread.tokens_used

    trend: list[dict[str, object]] = []
    for offset in range(days):
        current_day = start_day + timedelta(days=offset)
        trend.append({"date": current_day.isoformat(), "tokens": day_map.get(current_day, 0)})
    return trend
