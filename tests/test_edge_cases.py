"""Inputs that tend to break text processing."""

import pytest
from synthetic import AADHAAR, KITCHEN_SINK, PAN, PHONE, UPI

from kavach import Kavach


@pytest.fixture
def session():
    return Kavach().session()


def test_windows_line_endings(session):
    text = f"PAN {PAN}\r\nUPI {UPI}\r\n"
    masked = session.mask(text)
    assert masked == "PAN [PAN_1]\r\nUPI [UPI_1]\r\n"
    assert session.unmask(masked) == text


def test_aadhaar_split_across_lines_in_pasted_form(session):
    text = f"Aadhaar:\n{AADHAAR[:4]}\n{AADHAAR[4:8]}\n{AADHAAR[8:]}"
    assert session.mask(text) == "Aadhaar:\n[AADHAAR_1]"


def test_surrounded_by_devanagari_and_emoji(session):
    text = f"🙏 मेरा पैन {PAN} है, फ़ोन {PHONE} 😊"
    masked = session.mask(text)
    assert masked == "🙏 मेरा पैन [PAN_1] है, फ़ोन [PHONE_1] 😊"
    assert session.unmask(masked) == text


def test_markdown_and_json_wrappers(session):
    text = f'```\n{{"pan": "{PAN}", "upi": "{UPI}"}}\n```'
    assert session.mask(text) == '```\n{"pan": "[PAN_1]", "upi": "[UPI_1]"}\n```'


def test_values_back_to_back(session):
    assert session.mask(f"{PAN},{UPI};{PAN}") == "[PAN_1],[UPI_1];[PAN_1]"


def test_whitespace_only(session):
    assert session.mask(" \n\t ") == " \n\t "


def test_hundreds_of_values(session):
    text = " ".join(f"{i}: {PAN}" for i in range(300))
    masked = session.mask(text)
    assert masked.count("[PAN_1]") == 300
    assert session.unmask(masked) == text


def test_many_distinct_values_numbered_in_order(session):
    pans = [f"ABCPE{i:04d}F" for i in range(25)]
    masked = session.mask(" ".join(pans))
    assert masked.split() == [f"[PAN_{i + 1}]" for i in range(25)]


def test_mask_is_idempotent(session):
    once = session.mask(KITCHEN_SINK)
    assert session.mask(once) == once
