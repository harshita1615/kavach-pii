"""MCP server: lets an AI assistant check and redact Indian PII.

    pip install "kavach-pii[mcp]"
    kavach-mcp --root C:\\data        # stdio; add it to Claude Desktop, Claude Code, ...

Any text the assistant passes to a tool, it has already read. The privacy gain
is in the file tools: scan_file reports types and positions only, and
redact_file writes a copy with placeholders that the assistant reads instead
of the original, so raw values never enter the conversation.

Tool results never contain detected values. Files are read and written only
inside the --root folders, and an input file is never overwritten.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from kavach import __version__
from kavach.cli import detection_options
from kavach.engine import DEFAULT_THRESHOLD
from kavach.kavach import Kavach
from kavach.report import build as build_report

MAX_FILE_BYTES = 10 * 1024 * 1024
INSTALL_HINT = 'Kavach\'s MCP server needs the mcp extra: pip install "kavach-pii[mcp]"'

INSTRUCTIONS = (
    "Kavach detects Indian personal data (Aadhaar, PAN, UPI ID, IFSC, bank account, phone, "
    "GSTIN, email) and replaces it with placeholders such as [PAN_1]. Before reading a file that "
    "may contain customer or personal data, call scan_file; if it finds anything, call "
    "redact_file and read the redacted copy instead of the original. Before sending text "
    "somewhere else (a message, email, ticket, log or commit), call redact_text. Results never "
    "include the detected values. Keep placeholders exactly as written and do not guess the "
    "original values."
)


class AccessError(Exception):
    """A path or file the server refuses to use. The message names the path,
    never the file's contents."""


class Workspace:
    """The folders the server may read from and write to."""

    def __init__(self, roots: list[Path]) -> None:
        if not roots:
            raise ValueError("at least one root folder is required")
        self.roots = [root.resolve(strict=True) for root in roots]
        for root in self.roots:
            if not root.is_dir():
                raise ValueError(f"{root}: not a folder")

    def _inside(self, path: Path) -> bool:
        return any(path == root or path.is_relative_to(root) for root in self.roots)

    def _resolve(self, raw: str) -> Path:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = self.roots[0] / path
        # resolve() follows symlinks and "..", so the check below sees the real target.
        path = path.resolve()
        if not self._inside(path):
            raise AccessError(f"{raw}: outside the allowed folders ({self.describe()})")
        return path

    def describe(self) -> str:
        return ", ".join(str(root) for root in self.roots)

    def read(self, raw: str) -> tuple[Path, str]:
        path = self._resolve(raw)
        if not path.is_file():
            raise AccessError(f"{raw}: file not found")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise AccessError(f"{raw}: larger than {MAX_FILE_BYTES // (1024 * 1024)} MB")
        try:
            # utf-8-sig drops the byte-order mark Windows tools often add.
            return path, path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raise AccessError(f"{raw}: not a UTF-8 text file") from None
        except OSError as exc:
            raise AccessError(f"{raw}: {exc.strerror}") from None

    def write(self, raw: str, text: str, source: Path, overwrite: bool) -> Path:
        path = self._resolve(raw)
        if path == source:
            raise AccessError(f"{raw}: will not overwrite the input file")
        if not path.parent.is_dir():
            raise AccessError(f"{raw}: folder does not exist")
        try:
            # touch(exist_ok=False) fails atomically if the file appeared meanwhile.
            path.touch(exist_ok=overwrite)
            path.write_text(text, encoding="utf-8")
        except FileExistsError:
            raise AccessError(f"{raw}: already exists; pass overwrite=true to replace it") from None
        except OSError as exc:
            raise AccessError(f"{raw}: {exc.strerror}") from None
        return path


def default_output(path: Path) -> Path:
    """customers.csv -> customers.redacted.csv"""
    return path.with_name(f"{path.stem}.redacted{path.suffix}")


def build_server(
    workspace: Workspace,
    entities: list[str] | None = None,
    threshold: float = DEFAULT_THRESHOLD,
):
    """The MCP server with Kavach's tools. Requires the mcp extra."""
    try:
        from mcp.server.mcpserver import MCPServer
        from mcp.server.mcpserver.exceptions import ToolError
        from mcp.types import ToolAnnotations
    except ImportError:
        raise ImportError(INSTALL_HINT) from None

    # Redact mode: placeholders without a mapping, so nothing is ever restorable.
    kavach = Kavach(entities=entities, mode="redact", threshold=threshold)

    def redact(text: str) -> tuple[str, dict[str, int]]:
        session = kavach.session()
        return session.mask(text), session.counts

    server = MCPServer(
        name="kavach",
        title="Kavach: Indian PII shield",
        instructions=INSTRUCTIONS,
        version=__version__,
        website_url="https://github.com/harshita1615/kavach-pii",
    )
    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    pure = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)
    writes = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)

    @server.tool(annotations=pure)
    def scan_text(text: str) -> dict[str, Any]:
        """Find Indian PII in text. Returns each item's type, line, column, character
        offsets and confidence, plus counts per type. Never returns the values."""
        return build_report(text, kavach.scan(text))

    @server.tool(annotations=pure)
    def redact_text(text: str) -> dict[str, Any]:
        """Replace Indian PII in text with placeholders such as [PAN_1] or [PHONE_2].
        Use before sending text anywhere else. The originals cannot be restored."""
        redacted, counts = redact(text)
        return {"text": redacted, "count": sum(counts.values()), "counts": counts}

    @server.tool(annotations=read_only)
    def scan_file(path: str) -> dict[str, Any]:
        """Check a UTF-8 text file for Indian PII without reading it into the
        conversation. Returns types, line and column numbers and counts, never the
        values. Relative paths are resolved against the first allowed folder."""
        try:
            resolved, text = workspace.read(path)
        except AccessError as exc:
            raise ToolError(str(exc)) from None
        return {"file": str(resolved), **build_report(text, kavach.scan(text))}

    @server.tool(annotations=writes)
    def redact_file(
        path: str, output_path: str | None = None, overwrite: bool = False
    ) -> dict[str, Any]:
        """Write a copy of a UTF-8 text file with Indian PII replaced by placeholders,
        then read that copy instead of the original. output_path defaults to
        <name>.redacted.<ext> next to the input. The input file is never changed.
        Returns the output path and counts per type, never the values."""
        try:
            source, text = workspace.read(path)
            target = output_path or str(default_output(source))
            redacted, counts = redact(text)
            written = workspace.write(target, redacted, source, overwrite)
        except AccessError as exc:
            raise ToolError(str(exc)) from None
        return {
            "input": str(source),
            "output": str(written),
            "count": sum(counts.values()),
            "counts": counts,
        }

    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kavach-mcp",
        description="Run Kavach as an MCP server over stdio.",
        parents=[detection_options()],
    )
    parser.add_argument("--version", action="version", version=f"kavach-mcp {__version__}")
    parser.add_argument(
        "--root",
        action="append",
        type=Path,
        metavar="FOLDER",
        help="folder the file tools may read and write; repeat for more "
        "(default: the current folder)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # stdout carries the MCP protocol, so errors go to stderr via SystemExit.
    try:
        workspace = Workspace(args.root or [Path.cwd()])
        server = build_server(workspace, args.entities, args.threshold)
    except FileNotFoundError as exc:
        raise SystemExit(f"kavach-mcp: error: {exc.filename}: folder not found") from None
    except (ImportError, ValueError) as exc:
        raise SystemExit(f"kavach-mcp: error: {exc}") from None
    server.run("stdio")
    return 0


if __name__ == "__main__":
    sys.exit(main())
