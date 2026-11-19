"""Command line interface for agentsheet."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Sequence

from . import __version__
from .sheet import (
    SheetError,
    build_sheet,
    compare,
    has_drift,
    parse_sheet,
    render_diff,
    render_json,
    verify,
)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE_ERROR = 2


def _read_sheet(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return parse_sheet(handle.read())
    except (OSError, IOError) as exc:
        raise SheetError("cannot read sheet %s: %s" % (path, exc))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentsheet",
        description=(
            "Produce and verify a portable, offline spec sheet for a "
            "repository's AI agent setup. Never performs network calls."
        ),
    )
    parser.add_argument("--version", action="version", version="agentsheet %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="generate a spec sheet for a repository")
    gen.add_argument("repo", help="path to the repository to scan")
    gen.add_argument("-o", "--output", help="write JSON to this file instead of stdout")
    gen.add_argument(
        "--with-timestamp",
        action="store_true",
        help="include a generated_at timestamp (omitted by default for determinism)",
    )

    ver = sub.add_parser("verify", help="verify a repository against a spec sheet")
    ver.add_argument("repo", help="path to the repository to check")
    ver.add_argument("sheet", help="path to a previously generated agentsheet.json")

    dif = sub.add_parser("diff", help="compare two spec sheets")
    dif.add_argument("sheet_a", help="first sheet (baseline)")
    dif.add_argument("sheet_b", help="second sheet (current)")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "generate":
            if not os.path.isdir(args.repo):
                raise SheetError("not a directory: %s" % args.repo)
            sheet = build_sheet(args.repo, with_timestamp=args.with_timestamp)
            output = render_json(sheet)
            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as handle:
                        handle.write(output + "\n")
                except (OSError, IOError) as exc:
                    raise SheetError("cannot write %s: %s" % (args.output, exc))
            else:
                print(output)
            return EXIT_OK

        if args.command == "verify":
            if not os.path.isdir(args.repo):
                raise SheetError("not a directory: %s" % args.repo)
            sheet = _read_sheet(args.sheet)
            delta = verify(args.repo, sheet)
            print(render_diff(delta, old_label="sheet", new_label=args.repo))
            return EXIT_DRIFT if has_drift(delta) else EXIT_OK

        if args.command == "diff":
            sheet_a = _read_sheet(args.sheet_a)
            sheet_b = _read_sheet(args.sheet_b)
            delta = compare(sheet_a, sheet_b)
            print(render_diff(delta, old_label=args.sheet_a, new_label=args.sheet_b))
            return EXIT_OK

        parser.error("unknown command")
        return EXIT_USAGE_ERROR

    except SheetError as exc:
        print("agentsheet: error: %s" % exc, file=sys.stderr)
        return EXIT_USAGE_ERROR


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
