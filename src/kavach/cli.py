"""Command-line interface.

    kavach scan [FILE ...]          report PII by type and position (never the values)
    kavach redact [FILE] [-o OUT]   write the text with PII replaced by placeholders

FILE defaults to "-" (stdin). scan exits 1 when anything is found, so it can be
used as a pre-commit or CI check.

There is no "mask" command: restoring later would need the mapping saved to
disk, which Kavach never does. Use the Python API for reversible masking.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from kavach import __version__
from kavach.engine import DEFAULT_THRESHOLD
from kavach.kavach import Kavach
from kavach.report import build as build_report
from kavach.types import Detection, EntityType

EXIT_CLEAN = 0
EXIT_FOUND = 1
EXIT_ERROR = 2


class CliError(Exception):
    pass


def _read(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    path = Path(source)
    try:
        # utf-8-sig drops the byte-order mark Windows tools often add.
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise CliError(f"{source}: file not found") from None
    except UnicodeDecodeError:
        raise CliError(f"{source}: not a UTF-8 text file") from None
    except OSError as exc:
        raise CliError(f"{source}: {exc.strerror}") from None


def _report(source: str, text: str, detections: list[Detection]) -> dict:
    return {"file": source, **build_report(text, detections)}


def _print_report(report: dict) -> None:
    name = "<stdin>" if report["file"] == "-" else report["file"]
    if not report["count"]:
        print(f"{name}: no PII found")
        return
    print(f"{name}: {report['count']} item(s) found")
    for item in report["items"]:
        position = f"line {item['line']}, col {item['column']}"
        print(f"  {position:<20} {item['type']:<13} score {item['score']:.2f}")
    summary = ", ".join(f"{t} {n}" for t, n in sorted(report["counts"].items()))
    print(f"  summary: {summary}")


def _cmd_scan(kavach: Kavach, args: argparse.Namespace) -> int:
    reports = []
    for source in args.files:
        text = _read(source)
        reports.append(_report(source, text, kavach.scan(text)))
    if args.json:
        print(json.dumps(reports if len(reports) > 1 else reports[0], indent=2))
    else:
        for report in reports:
            _print_report(report)
    return EXIT_FOUND if any(r["count"] for r in reports) else EXIT_CLEAN


def _cmd_redact(kavach: Kavach, args: argparse.Namespace) -> int:
    redacted = kavach.redact(_read(args.file))
    if args.output:
        try:
            Path(args.output).write_text(redacted, encoding="utf-8")
        except OSError as exc:
            raise CliError(f"{args.output}: {exc.strerror}") from None
    else:
        sys.stdout.write(redacted)
    return EXIT_CLEAN


def _entities(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    entity_names = ", ".join(e.value for e in EntityType)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--entities",
        type=_entities,
        metavar="LIST",
        help=f"comma-separated entity types to detect (default: all). One of: {entity_names}",
    )
    common.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"minimum confidence, 0-1 (default: {DEFAULT_THRESHOLD})",
    )

    parser = argparse.ArgumentParser(
        prog="kavach", description="Detect and redact Indian PII in text."
    )
    parser.add_argument("--version", action="version", version=f"kavach {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser(
        "scan",
        parents=[common],
        help="report PII by type and position (values are never printed)",
        description="Report PII by type and position. Exits 1 if anything is found.",
    )
    scan.add_argument("files", nargs="*", default=["-"], help="files to scan (default: stdin)")
    scan.add_argument("--json", action="store_true", help="output JSON")
    scan.set_defaults(handler=_cmd_scan)

    redact = sub.add_parser(
        "redact",
        parents=[common],
        help="replace PII with placeholders",
        description="Write the text with PII replaced by placeholders such as [PAN_1].",
    )
    redact.add_argument("file", nargs="?", default="-", help="file to redact (default: stdin)")
    redact.add_argument("-o", "--output", help="write to this file instead of stdout")
    redact.set_defaults(handler=_cmd_redact)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to a legacy code page; Hindi text needs UTF-8.
    # utf-8-sig on stdin drops the byte-order mark PowerShell adds when piping.
    for stream, encoding in ((sys.stdout, "utf-8"), (sys.stdin, "utf-8-sig")):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding=encoding)

    args = build_parser().parse_args(argv)
    try:
        kavach = Kavach(entities=args.entities, threshold=args.threshold)
        return args.handler(kavach, args)
    except (CliError, ValueError) as exc:
        print(f"kavach: error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
