import io
import json
import subprocess
import sys

import pytest
from synthetic import KITCHEN_SINK, PAN, UPI

from kavach.cli import EXIT_CLEAN, EXIT_ERROR, EXIT_FOUND, main

ALL_VALUES_IN_SINK = [PAN, UPI, "rahul@example.com", "30012345678"]


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "chat.txt"
    path.write_text(f"hello\nmy PAN is {PAN}\nrefund to {UPI}\n", encoding="utf-8")
    return path


# --- scan --------------------------------------------------------------------


def test_scan_reports_types_and_positions(sample, capsys):
    assert main(["scan", str(sample)]) == EXIT_FOUND
    out = capsys.readouterr().out
    assert "2 item(s) found" in out
    assert "line 2, col 11" in out
    assert "PAN" in out and "UPI" in out
    assert "summary: PAN 1, UPI 1" in out


def test_scan_never_prints_values(tmp_path, capsys):
    path = tmp_path / "sink.txt"
    path.write_text(KITCHEN_SINK, encoding="utf-8")
    main(["scan", str(path)])
    main(["scan", "--json", str(path)])
    out = capsys.readouterr().out
    for value in ALL_VALUES_IN_SINK:
        assert value not in out


def test_scan_clean_file_exits_zero(tmp_path, capsys):
    path = tmp_path / "clean.txt"
    path.write_text("nothing to see", encoding="utf-8")
    assert main(["scan", str(path)]) == EXIT_CLEAN
    assert "no PII found" in capsys.readouterr().out


def test_scan_json(sample, capsys):
    main(["scan", "--json", str(sample)])
    report = json.loads(capsys.readouterr().out)
    assert report["count"] == 2
    assert report["counts"] == {"PAN": 1, "UPI": 1}
    assert report["items"][0] == {
        "type": "PAN",
        "line": 2,
        "column": 11,
        "start": 16,
        "end": 26,
        "score": report["items"][0]["score"],
    }


def test_scan_multiple_files(sample, tmp_path, capsys):
    clean = tmp_path / "clean.txt"
    clean.write_text("nothing", encoding="utf-8")
    assert main(["scan", "--json", str(sample), str(clean)]) == EXIT_FOUND
    reports = json.loads(capsys.readouterr().out)
    assert [r["count"] for r in reports] == [2, 0]


def test_scan_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"PAN {PAN}"))
    assert main(["scan"]) == EXIT_FOUND
    assert "<stdin>: 1 item(s) found" in capsys.readouterr().out


def test_scan_entity_filter(sample, capsys):
    main(["scan", "--json", "--entities", "upi", str(sample)])
    assert json.loads(capsys.readouterr().out)["counts"] == {"UPI": 1}


# --- redact ------------------------------------------------------------------


def test_redact_to_stdout(sample, capsys):
    assert main(["redact", str(sample)]) == EXIT_CLEAN
    assert capsys.readouterr().out == "hello\nmy PAN is [PAN_1]\nrefund to [UPI_1]\n"


def test_redact_to_file(sample, tmp_path):
    out = tmp_path / "out.txt"
    assert main(["redact", str(sample), "-o", str(out)]) == EXIT_CLEAN
    assert PAN not in out.read_text(encoding="utf-8")


def test_redact_keeps_hindi_text(tmp_path, capsys):
    path = tmp_path / "hi.txt"
    path.write_text(f"मेरा पैन {PAN} है", encoding="utf-8")
    main(["redact", str(path)])
    assert capsys.readouterr().out == "मेरा पैन [PAN_1] है"


def test_utf8_bom_is_ignored(tmp_path, capsys):
    path = tmp_path / "bom.txt"
    path.write_text(f"PAN {PAN}", encoding="utf-8-sig")
    main(["redact", str(path)])
    assert capsys.readouterr().out == "PAN [PAN_1]"
    main(["scan", "--json", str(path)])
    assert json.loads(capsys.readouterr().out)["items"][0]["column"] == 5


# --- errors ------------------------------------------------------------------


def test_missing_file(capsys):
    assert main(["scan", "does-not-exist.txt"]) == EXIT_ERROR
    assert "file not found" in capsys.readouterr().err


def test_binary_file(tmp_path, capsys):
    path = tmp_path / "bin.dat"
    path.write_bytes(b"\xff\xfe\x00\x81")
    assert main(["scan", str(path)]) == EXIT_ERROR
    assert "not a UTF-8 text file" in capsys.readouterr().err


def test_unknown_entity(sample, capsys):
    assert main(["scan", "--entities", "PASSPORT", str(sample)]) == EXIT_ERROR
    assert "unknown entity" in capsys.readouterr().err


def test_bad_threshold(sample, capsys):
    assert main(["scan", "--threshold", "2", str(sample)]) == EXIT_ERROR


def test_no_command_shows_usage(capsys):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_python_dash_m(sample):
    result = subprocess.run(
        [sys.executable, "-m", "kavach", "scan", str(sample)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == EXIT_FOUND
    assert "2 item(s) found" in result.stdout
