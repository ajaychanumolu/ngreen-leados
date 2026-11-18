"""SQLite file backup. Postgres backup is a database command, documented in the runbook."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def backup_sqlite(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _copy(source, destination)


def restore_sqlite(backup: Path, destination: Path) -> None:
    if not backup.is_file():
        raise FileNotFoundError(backup)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".restore")
    if temporary.exists():
        temporary.unlink()
    _copy(backup, temporary)
    temporary.replace(destination)


def _copy(source: Path, destination: Path) -> None:
    origin = sqlite3.connect(source)
    copy = sqlite3.connect(destination)
    try:
        origin.backup(copy)
    finally:
        copy.close()
        origin.close()
