"""Append-only audit log for chat agent activity: output/audit_trail.json.

That file is public on GitHub, so entries only ever identify a shopper as
"guest" or "user:<id>" (see models.AuditEntry) and every value logged here is
trimmed and redacted first — never a password, password hash, or the Portkey
API key.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from models import AuditEntry

ROOT = Path(__file__).resolve().parent
AUDIT_PATH = ROOT.parent / "output" / "audit_trail.json"

# If audit_trail.json is ever found unreadable (corrupted, hand-edited into
# invalid JSON, etc.), new entries land here instead of anywhere near the
# original file — see append_entries().
RECOVERY_PATH = ROOT.parent / "output" / "audit_trail.recovery.json"

TRIM_LIMIT = 300

logger = logging.getLogger("campus_customs.audit")


def _redact(text: str) -> str:
    """Strip the Portkey API key out of a log line, belt-and-suspenders in case
    it ever ends up embedded in a tool result or error message.
    """
    key = os.environ.get("PORTKEY_API_KEY")
    return text.replace(key, "[REDACTED]") if key else text


def _json_default(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def trim(value: object) -> str | None:
    """Render a tool argument/result as a short, redacted string for the log."""
    if value is None:
        return None
    text = value if isinstance(value, str) else json.dumps(value, default=_json_default, ensure_ascii=False)
    text = _redact(text)
    if len(text) > TRIM_LIMIT:
        text = text[:TRIM_LIMIT] + "...(trimmed)"
    return text


def _quarantine_unreadable(path: Path) -> None:
    """Copy (never move) whatever's currently at `path` to a timestamped
    sibling file, so nothing is lost even though it couldn't be parsed. The
    original file is left completely untouched by this — copying, not moving.
    """
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = path.with_name(f"{path.stem}.unreadable-{stamp}{path.suffix}")
    backup_path.write_bytes(path.read_bytes())
    logger.error("%s was unreadable — backed up to %s and left untouched", path, backup_path)


def _read_modify_write(path: Path, entries: list[AuditEntry]) -> None:
    """Append entries to `path` under an exclusive lock. Raises (without
    writing anything) if the existing content can't be parsed as a JSON
    array — this function never truncates a file unless it just successfully
    read that same file's current content as a valid JSON list.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # "a" creates the file if it's missing, without truncating any existing content.
    with open(path, "a", encoding="utf-8"):
        pass

    with open(path, "r+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            raw = f.read()
            existing = json.loads(raw) if raw.strip() else []
            if not isinstance(existing, list):
                raise ValueError(f"{path} does not contain a JSON array")
            existing.extend(entry.model_dump() for entry in entries)
            f.seek(0)
            f.truncate()
            json.dump(existing, f, indent=2, ensure_ascii=False)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def append_entries(entries: list[AuditEntry]) -> None:
    """Append entries to output/audit_trail.json — never wipes, truncates, or
    overwrites old entries, across runs, server restarts, or a format change
    (old entries missing newer fields like `run_id`/`event` sit right next to
    new ones just fine — a JSON array can mix objects with different keys).

    Safe for two chats (or two processes) writing at the same time: the
    read-modify-write is done under an exclusive file lock, so a concurrent
    writer blocks until it's done rather than racing and corrupting the file.

    If the file can't be parsed as a JSON array for any reason, this never
    touches it: it's backed up as-is to a timestamped sibling file, and the
    new entries go to output/audit_trail.recovery.json instead, so nothing
    old is lost and nothing new is silently dropped either.

    (Uses fcntl, so the lock is POSIX-only — fine for this project's mac/Linux
    dev environment, but would need an alternative lock on Windows.)
    """
    if not entries:
        return
    try:
        _read_modify_write(AUDIT_PATH, entries)
    except (json.JSONDecodeError, ValueError):
        _quarantine_unreadable(AUDIT_PATH)
        _read_modify_write(RECOVERY_PATH, entries)
