"""Discover AI-agent configuration files in a repository and hash them.

Discovery is entirely local and offline.  It looks for well-known instruction
file names, MCP configuration files, files under ``.workbuddy/``, and skill
folders (any directory containing a ``SKILL.md``).  Heavy/vendored directories
are skipped so scans stay fast and reproducible.
"""

from __future__ import annotations

import hashlib
import os
from typing import Dict, List, Tuple

# Directories never descended into.
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

# Exact relative paths that are always agent configuration when present.
KNOWN_FILES = {
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
    ".cursor/rules",  # directory, handled below
    "mcp.json",
    ".mcp.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
    ".workbuddy/mcp.json",
    "SKILL.md",
}

# Directories whose entire contents are considered agent configuration.
CONFIG_DIRS = {".workbuddy", ".cursor/rules"}


def _is_under_config_dir(rel: str) -> bool:
    return ".workbuddy" in rel.split("/") or rel.startswith(".cursor/rules/")


def discover(repo: str) -> List[str]:
    """Return a sorted list of POSIX-style relative paths of agent files."""
    if not os.path.isdir(repo):
        raise NotADirectoryError(repo)

    candidates: List[str] = []
    skill_md_paths: List[str] = []

    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        dirnames.sort()
        for filename in sorted(filenames):
            absolute = os.path.join(dirpath, filename)
            relative = os.path.relpath(absolute, repo).replace(os.sep, "/")
            candidates.append(relative)
            if filename == "SKILL.md":
                skill_md_paths.append(relative)

    # Skill folders: any file whose ancestor directory contains a SKILL.md.
    skill_dirs = {os.path.dirname(p) for p in skill_md_paths}

    selected = set()
    for rel in candidates:
        if rel in KNOWN_FILES or _is_under_config_dir(rel):
            selected.add(rel)
            continue
        parts = rel.split("/")
        ancestors = ["/".join(parts[:i]) for i in range(1, len(parts))]
        if any(ancestor in skill_dirs for ancestor in ancestors):
            selected.add(rel)

    return sorted(selected)


def hash_file(path: str, chunk_size: int = 65536) -> Tuple[str, int]:
    """Return ``(sha256_hexdigest, byte_size)`` for ``path``."""
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def snapshot(repo: str) -> Dict[str, dict]:
    """Build ``{relative_path: {sha256, size}}`` for all discovered files."""
    result: Dict[str, dict] = {}
    for rel in discover(repo):
        sha, size = hash_file(os.path.join(repo, *rel.split("/")))
        result[rel] = {"sha256": sha, "size": size}
    return result
