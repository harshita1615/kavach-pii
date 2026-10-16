import asyncio
import json
import sys

import pytest
from synthetic import AADHAAR_SPACED, BANK, EMAIL, GSTIN, IFSC, KITCHEN_SINK, PAN, PHONE, UPI

pytest.importorskip("mcp")

from mcp import Client, StdioServerParameters  # noqa: E402

from kavach import Kavach, mcp_server  # noqa: E402
from kavach.mcp_server import Workspace, build_server, main  # noqa: E402

VALUES = [AADHAAR_SPACED, PAN, UPI, IFSC, BANK, PHONE, EMAIL, GSTIN]
NOT_UTF8 = b"PAN ABCPE1234F \xff\xfe"


async def _call(server, tool, arguments):
    async with Client(server) as client:
        return await client.call_tool(tool, arguments)


def call(root, tool, arguments, **options):
    """Call a tool on a server limited to root. Returns (result, everything the
    client received as one string, for checking that no value leaked)."""
    result = asyncio.run(_call(build_server(Workspace([root]), **options), tool, arguments))
    received = json.dumps(result.structured_content) + "".join(c.text for c in result.content)
    return result, received


def assert_no_values(received):
    for value in VALUES:
        assert value not in received


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "sink.txt").write_text(KITCHEN_SINK, encoding="utf-8")
    return folder


# --- tools -------------------------------------------------------------------


def test_lists_four_tools_with_hints(root):
    async def tools():
        async with Client(build_server(Workspace([root]))) as client:
            return {t.name: t for t in (await client.list_tools()).tools}

    tools = asyncio.run(tools())
    assert set(tools) == {"scan_text", "redact_text", "scan_file", "redact_file"}
    for name in ("scan_text", "redact_text", "scan_file"):
        assert tools[name].annotations.read_only_hint is True
    assert tools["redact_file"].annotations.destructive_hint is False
    assert all(t.annotations.open_world_hint is False for t in tools.values())


def test_scan_text_reports_types_not_values(root):
    result, received = call(root, "scan_text", {"text": KITCHEN_SINK})
    assert not result.is_error
    report = result.structured_content
    assert report["count"] == 8
    assert set(report["counts"]) == {e.value for e in Kavach().entities}
    assert report["items"][0]["line"] == 1
    assert_no_values(received)


def test_redact_text(root):
    result, received = call(root, "redact_text", {"text": KITCHEN_SINK})
    out = result.structured_content
    assert out["text"] == Kavach().redact(KITCHEN_SINK)
    assert "[PAN_1]" in out["text"]
    assert out["count"] == 8
    assert_no_values(received)


def test_redact_text_clean_input(root):
    result, _ = call(root, "redact_text", {"text": "nothing to see"})
    assert result.structured_content == {"text": "nothing to see", "count": 0, "counts": {}}


def test_scan_file(root):
    result, received = call(root, "scan_file", {"path": "sink.txt"})
    report = result.structured_content
    assert report["file"] == str(root / "sink.txt")
    assert report["count"] == 8
    assert_no_values(received)


def test_scan_file_absolute_path(root):
    result, _ = call(root, "scan_file", {"path": str(root / "sink.txt")})
    assert result.structured_content["count"] == 8


def test_scan_file_drops_bom(root):
    (root / "bom.txt").write_text(f"PAN {PAN}", encoding="utf-8-sig")
    result, _ = call(root, "scan_file", {"path": "bom.txt"})
    assert result.structured_content["items"][0]["column"] == 5


def test_redact_file_default_output(root):
    result, received = call(root, "redact_file", {"path": "sink.txt"})
    out = result.structured_content
    written = root / "sink.redacted.txt"
    assert out["output"] == str(written)
    assert out["counts"]["PAN"] == 1
    assert written.read_text(encoding="utf-8") == Kavach().redact(KITCHEN_SINK)
    assert (root / "sink.txt").read_text(encoding="utf-8") == KITCHEN_SINK
    assert_no_values(received)


def test_redact_file_custom_output_in_subfolder(root):
    (root / "safe").mkdir()
    result, _ = call(root, "redact_file", {"path": "sink.txt", "output_path": "safe/out.txt"})
    assert result.structured_content["output"] == str(root / "safe" / "out.txt")
    assert "[UPI_1]" in (root / "safe" / "out.txt").read_text(encoding="utf-8")


def test_redact_file_no_suffix(root):
    (root / "notes").write_text(f"PAN {PAN}", encoding="utf-8")
    call(root, "redact_file", {"path": "notes"})
    assert (root / "notes.redacted").read_text(encoding="utf-8") == "PAN [PAN_1]"


def test_redact_file_respects_entities(root):
    result, _ = call(root, "redact_file", {"path": "sink.txt"}, entities=["PAN"])
    assert result.structured_content["counts"] == {"PAN": 1}
    text = (root / "sink.redacted.txt").read_text(encoding="utf-8")
    assert "PAN [PAN_1]" in text and UPI in text and GSTIN in text  # GSTIN embeds the PAN


def test_redact_file_refuses_existing_output(root):
    existing = root / "sink.redacted.txt"
    existing.write_text("keep me", encoding="utf-8")
    result, received = call(root, "redact_file", {"path": "sink.txt"})
    assert result.is_error
    assert "already exists" in received
    assert existing.read_text(encoding="utf-8") == "keep me"

    result, _ = call(root, "redact_file", {"path": "sink.txt", "overwrite": True})
    assert not result.is_error
    assert "[PAN_1]" in existing.read_text(encoding="utf-8")


@pytest.mark.parametrize("output", ["sink.txt", "./sub/../sink.txt"])
def test_redact_file_never_overwrites_input(root, output):
    result, received = call(
        root, "redact_file", {"path": "sink.txt", "output_path": output, "overwrite": True}
    )
    assert result.is_error
    assert "will not overwrite the input" in received
    assert (root / "sink.txt").read_text(encoding="utf-8") == KITCHEN_SINK


# --- file access -------------------------------------------------------------


def test_refuses_paths_outside_root(root):
    outside = root.parent / "secret.txt"
    outside.write_text(KITCHEN_SINK, encoding="utf-8")
    for path in ("../secret.txt", str(outside)):
        result, received = call(root, "scan_file", {"path": path})
        assert result.is_error
        assert "outside the allowed folders" in received
        assert_no_values(received)


def test_refuses_output_outside_root(root):
    result, received = call(root, "redact_file", {"path": "sink.txt", "output_path": "../leak.txt"})
    assert result.is_error
    assert "outside the allowed folders" in received
    assert not (root.parent / "leak.txt").exists()


def test_refuses_symlink_escaping_root(root):
    outside = root.parent / "secret.txt"
    outside.write_text(KITCHEN_SINK, encoding="utf-8")
    link = root / "link.txt"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("creating symlinks is not permitted here")
    result, received = call(root, "scan_file", {"path": "link.txt"})
    assert result.is_error
    assert "outside the allowed folders" in received


def test_missing_file(root):
    result, received = call(root, "scan_file", {"path": "nope.txt"})
    assert result.is_error
    assert "nope.txt: file not found" in received


def test_folder_is_not_a_file(root):
    result, received = call(root, "scan_file", {"path": "."})
    assert result.is_error
    assert "file not found" in received


def test_output_folder_must_exist(root):
    result, received = call(
        root, "redact_file", {"path": "sink.txt", "output_path": "missing/out.txt"}
    )
    assert result.is_error
    assert "folder does not exist" in received


def test_not_utf8(root):
    (root / "bin.dat").write_bytes(NOT_UTF8)
    result, received = call(root, "scan_file", {"path": "bin.dat"})
    assert result.is_error
    assert "not a UTF-8 text file" in received
    assert PAN not in received


def test_too_large(root, monkeypatch):
    monkeypatch.setattr(mcp_server, "MAX_FILE_BYTES", 10)
    result, received = call(root, "scan_file", {"path": "sink.txt"})
    assert result.is_error
    assert "larger than" in received


def test_multiple_roots(root, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "b.txt").write_text(f"PAN {PAN}", encoding="utf-8")
    server = build_server(Workspace([root, other]))
    result = asyncio.run(_call(server, "scan_file", {"path": str(other / "b.txt")}))
    assert result.structured_content["counts"] == {"PAN": 1}


def test_workspace_rejects_bad_roots(tmp_path):
    with pytest.raises(FileNotFoundError):
        Workspace([tmp_path / "missing"])
    file = tmp_path / "f.txt"
    file.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="not a folder"):
        Workspace([file])
    with pytest.raises(ValueError, match="at least one"):
        Workspace([])


# --- command line ------------------------------------------------------------


def test_main_missing_root(tmp_path):
    with pytest.raises(SystemExit, match="folder not found"):
        main(["--root", str(tmp_path / "missing")])


def test_main_bad_entity(tmp_path):
    with pytest.raises(SystemExit, match="kavach-mcp: error"):
        main(["--root", str(tmp_path), "--entities", "NOPE"])


def test_stdio_end_to_end(root):
    """The real command over stdio: nothing but protocol messages on stdout."""
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "kavach.mcp_server", "--root", str(root)]
    )

    async def run():
        async with Client(params) as client:
            return await client.call_tool("scan_file", {"path": "sink.txt"})

    result = asyncio.run(run())
    assert result.structured_content["count"] == 8
