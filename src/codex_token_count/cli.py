from __future__ import annotations

import argparse
import json
from datetime import datetime

from .analytics import build_daily_trend, build_summary, summarize_projects, top_sessions
from .datasource import load_threads, load_token_events
from .models import ThreadRecord, TokenEvent
from .presenters import (
    build_console,
    print_project_view,
    print_rows_table,
    print_session_view,
    print_summary_view,
    print_trend_view,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-token", description="Analyze local Codex token usage.")
    parser.add_argument("--codex-home", help="Override Codex data directory. Defaults to ~/.codex.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output JSON.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="Show global usage summary.")

    top_parser = subparsers.add_parser("top", help="Show highest-consumption sessions.")
    top_parser.add_argument("--limit", type=int, default=10)

    subparsers.add_parser("projects", help="Show token usage grouped by cwd.")

    project_parser = subparsers.add_parser("project", help="Show sessions for a specific cwd.")
    project_parser.add_argument("path", help="Exact cwd path to inspect.")
    project_parser.add_argument("--limit", type=int, default=20)

    trend_parser = subparsers.add_parser("trend", help="Show daily token trend.")
    trend_parser.add_argument("--days", type=int, default=7)

    session_parser = subparsers.add_parser("session", help="Show details for one session.")
    session_parser.add_argument("session_id", help="Session ID or unique prefix.")
    session_parser.add_argument("--events", type=int, default=10, help="Number of recent token events to show.")

    return parser


def _serialize(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_serialize))


def _filter_threads_by_project(threads: list[ThreadRecord], path: str) -> list[ThreadRecord]:
    return [thread for thread in threads if thread.cwd == path]


def _resolve_session(threads: list[ThreadRecord], session_id: str) -> ThreadRecord | None:
    exact_match = next((thread for thread in threads if thread.session_id == session_id), None)
    if exact_match is not None:
        return exact_match

    prefix_matches = [thread for thread in threads if thread.session_id.startswith(session_id)]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    return None


def _session_event_rows(events: list[TokenEvent], limit: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_total = 0
    for event in events:
        delta = max(event.total_tokens - previous_total, 0)
        rows.append(
            {
                "timestamp": event.timestamp,
                "total_tokens": event.total_tokens,
                "delta_tokens": delta,
                "input_tokens": event.input_tokens,
                "cached_input_tokens": event.cached_input_tokens,
                "output_tokens": event.output_tokens,
                "reasoning_output_tokens": event.reasoning_output_tokens,
            }
        )
        previous_total = event.total_tokens
    return rows[-limit:]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    console = None if args.as_json else build_console()

    threads = load_threads(args.codex_home)
    if args.command == "summary":
        summary = build_summary(threads)
        if args.as_json:
            _print_json(summary)
            return 0
        trend_rows = build_daily_trend(threads, [], days=7)
        print_summary_view(console, summary, trend_rows)
        return 0

    if args.command == "top":
        rows = [
            {
                "session_id": item.session_id,
                "tokens_used": item.tokens_used,
                "updated_at": item.updated_at,
                "cwd": item.cwd,
                "title": item.title,
            }
            for item in top_sessions(threads, limit=max(args.limit, 1))
        ]
        if args.as_json:
            _print_json(rows)
            return 0
        print_rows_table(
            console,
            rows,
            [
                ("session_id", "Session ID"),
                ("tokens_used", "Tokens"),
                ("updated_at", "Updated At"),
                ("cwd", "CWD"),
                ("title", "Title"),
            ],
            title="Top Sessions",
        )
        return 0

    if args.command == "projects":
        rows = summarize_projects(threads)
        if args.as_json:
            _print_json(rows)
            return 0
        print_rows_table(
            console,
            rows,
            [
                ("cwd", "CWD"),
                ("sessions", "Sessions"),
                ("tokens_used", "Tokens"),
                ("last_updated_at", "Last Updated At"),
            ],
            title="Projects",
        )
        return 0

    if args.command == "project":
        project_threads = _filter_threads_by_project(threads, args.path)
        summary = build_summary(project_threads)
        rows = [
            {
                "session_id": item.session_id,
                "tokens_used": item.tokens_used,
                "updated_at": item.updated_at,
                "title": item.title,
            }
            for item in top_sessions(project_threads, limit=max(args.limit, 1))
        ]
        if args.as_json:
            _print_json({"path": args.path, "summary": summary, "sessions": rows})
            return 0
        print_project_view(console, args.path, summary, rows)
        return 0

    if args.command == "trend":
        token_events = load_token_events(args.codex_home)
        rows = build_daily_trend(threads, token_events, days=max(args.days, 1))
        if args.as_json:
            _print_json(rows)
            return 0
        print_trend_view(console, rows)
        return 0

    if args.command == "session":
        thread = _resolve_session(threads, args.session_id)
        if thread is None:
            parser.error(f"Session not found or not unique: {args.session_id}")

        token_events = load_token_events(args.codex_home)
        session_events = [event for event in token_events if event.session_id == thread.session_id]
        event_rows = _session_event_rows(session_events, limit=max(args.events, 1))

        payload = {
            "session": {
                "session_id": thread.session_id,
                "title": thread.title,
                "cwd": thread.cwd,
                "model_provider": thread.model_provider,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "tokens_used": thread.tokens_used,
            },
            "token_events": event_rows,
        }
        if args.as_json:
            _print_json(payload)
            return 0
        print_session_view(console, payload["session"], event_rows, len(session_events))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
