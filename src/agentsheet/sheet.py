"""Build, render, compare and verify agentsheet JSON documents."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from . import __version__
from .scanner import snapshot

SCHEMA_VERSION = 1


class SheetError(Exception):
    """Raised when a sheet file is malformed or has an unsupported schema."""


def build_sheet(repo: str, with_timestamp: bool = False) -> dict:
    """Create a deterministic sheet for ``repo``.

    No timestamps are included unless ``with_timestamp`` is True, so output is
    byte-for-byte stable across machines and runs.
    """
    sheet = {
        "schema_version": SCHEMA_VERSION,
        "generator": "agentsheet/%s" % __version__,
        "files": snapshot(repo),
    }
    if with_timestamp:
        sheet["generated_at"] = datetime.now(timezone.utc).isoformat()
    return sheet


def render_json(sheet: dict) -> str:
    """Render a sheet as deterministic, sorted, indented JSON."""
    return json.dumps(sheet, indent=2, sort_keys=True, ensure_ascii=False)


def parse_sheet(text: str) -> dict:
    """Parse and validate a sheet document from JSON text."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SheetError("invalid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise SheetError("sheet must be a JSON object")
    files = data.get("files")
    if not isinstance(files, dict):
        raise SheetError("sheet is missing a 'files' object")
    for path, entry in files.items():
        if not isinstance(entry, dict) or "sha256" not in entry:
            raise SheetError("invalid entry for file %r" % path)
    return data


def compare(old: dict, new: dict) -> Dict[str, List[str]]:
    """Compare two sheets and return added/removed/modified path lists."""
    old_files = old.get("files", {})
    new_files = new.get("files", {})
    old_paths = set(old_files)
    new_paths = set(new_files)

    added = sorted(new_paths - old_paths)
    removed = sorted(old_paths - new_paths)
    modified = sorted(
        path
        for path in (old_paths & new_paths)
        if old_files[path] != new_files[path]
    )
    return {"added": added, "removed": removed, "modified": modified}


def verify(repo: str, sheet: dict) -> Dict[str, List[str]]:
    """Re-scan ``repo`` and compare it against a recorded ``sheet``."""
    current = build_sheet(repo, with_timestamp=False)
    return compare(sheet, current)


def render_diff(delta: Dict[str, List[str]], old_label: str = "A", new_label: str = "B") -> str:
    """Render a comparison result as a human-readable report."""
    lines = ["agentsheet diff (%s -> %s)" % (old_label, new_label)]
    for key, title in (("added", "ADDED"), ("removed", "REMOVED"), ("modified", "MODIFIED")):
        paths = delta.get(key, [])
        lines.append("")
        lines.append("%s (%d)" % (title, len(paths)))
        if paths:
            lines.extend("  + %s" % path for path in paths)
        else:
            lines.append("  (none)")
    return "\n".join(lines)


def has_drift(delta: Dict[str, List[str]]) -> bool:
    """True if any added/removed/modified paths are present."""
    return bool(delta.get("added") or delta.get("removed") or delta.get("modified"))
