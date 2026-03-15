from __future__ import annotations

from pathlib import Path

from ..paths import resolve_codex_paths
from ..models import ThreadRecord, TokenEvent
from .session_jsonl_reader import read_token_events
from .sqlite_reader import read_threads


def load_threads(codex_home: str | Path | None = None) -> list[ThreadRecord]:
    paths = resolve_codex_paths(codex_home)
    return read_threads(paths.state_db)


def load_token_events(codex_home: str | Path | None = None) -> list[TokenEvent]:
    paths = resolve_codex_paths(codex_home)
    return read_token_events(paths.sessions_dir)
