# agentsheet

**Portable, verifiable, offline spec sheet for a repository's AI agent setup.**

`agentsheet` records exactly how a repository configures its AI agents —
`CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md`,
`.workbuddy/`, skill folders, and MCP configuration — into a single small JSON
file. Later, it can re-scan the repository and tell you precisely what changed.

It is fully offline and uses only the Python standard library (3.9+). No
network calls, no dependencies, no telemetry. The generated sheet contains no
timestamps by default, so the output is byte-for-byte deterministic and safe
to commit to git.

## The problem

AI-agent configuration is scattered across many files and folders. When a repo
is cloned on another machine — or a teammate edits an instruction file — it is
hard to answer "is the agent setup still the same?". `agentsheet` turns that
setup into a verifiable fingerprint you can diff and check in CI.

## Install

```console
pip install .
```

Or run it directly from a checkout — a tiny root-level shim makes the bare
command work without installing:

```console
python -m agentsheet --help
```

(The real implementation lives in `src/agentsheet`; the shim delegates to it.
`PYTHONPATH=src python -m agentsheet ...` also works.)

## Commands

```console
agentsheet generate <repo> [-o sheet.json] [--with-timestamp]
agentsheet verify   <repo> <sheet.json>
agentsheet diff     <sheetA.json> <sheetB.json>
```

### `generate`

Scan `<repo>` and print a deterministic JSON sheet to stdout, or write it to a
file with `-o`. The sheet records each discovered file's SHA-256 digest and
byte size:

```json
{
  "files": {
    "CLAUDE.md": {
      "sha256": "9f2c...",
      "size": 128
    }
  },
  "generator": "agentsheet/0.1.0",
  "schema_version": 1
}
```

By default there is **no timestamp** — two runs on identical content produce
identical bytes. Pass `--with-timestamp` if you want a `generated_at` field.

### `verify`

Re-scan `<repo>` and compare against a saved sheet. Prints an `ADDED` /
`REMOVED` / `MODIFIED` report and exits **1** if any drift is found, **0** if
the repository is clean:

```console
$ agentsheet verify . agentsheet.json
agentsheet diff (sheet -> .)

ADDED (0)
  (none)

REMOVED (0)
  (none)

MODIFIED (1)
  + CLAUDE.md
```

### `diff`

Compare two saved sheets and print the same human-readable report. Exits 0 on
a successful comparison; differences are the expected output, not an error.

## What is scanned

* Instruction files: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`,
  `.github/copilot-instructions.md`, `SKILL.md`
* MCP configuration: `mcp.json`, `.mcp.json`, `.cursor/mcp.json`,
  `.vscode/mcp.json`, `.workbuddy/mcp.json`
* Everything under `.workbuddy/` and `.cursor/rules/`
* Skill folders — any directory containing a `SKILL.md` (all files in it)

Vendored/heavy directories (`.git`, `node_modules`, `__pycache__`, virtualenvs,
`dist`, `build`, …) are skipped. Paths are stored as POSIX-style relative
paths and sorted, so sheets are stable across operating systems.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | OK (clean verification, successful generate/diff) |
| 1 | drift detected by `verify` |
| 2 | usage / input error (bad path, missing or malformed sheet) |

## Repo layout

```
src/agentsheet/   package (scanner, sheet logic, CLI)
tests/            unittest suite using temporary repo fixtures
```

## License

MIT — see [LICENSE](LICENSE).
