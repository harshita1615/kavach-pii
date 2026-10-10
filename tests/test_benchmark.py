"""The benchmark dataset is valid, and the metrics compute what they claim."""

import json
from pathlib import Path

import pytest

from benchmark.metrics import Counts, Span, false_alarms, masked_counts, strict_counts
from kavach.detectors.pan import HOLDER_TYPES
from kavach.validators import gstin_checksum, verhoeff

DATASET_DIR = Path(__file__).parent.parent / "benchmark" / "dataset"
SPLITS = {"dev": "kavach_bench_v1.jsonl", "holdout": "kavach_bench_v1_holdout.jsonl"}
TYPES = {"AADHAAR", "PAN", "UPI", "IFSC", "BANK_ACCOUNT", "PHONE", "GSTIN", "EMAIL"}


def load(split):
    with (DATASET_DIR / SPLITS[split]).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@pytest.fixture(scope="module", params=list(SPLITS))
def records(request):
    return load(request.param)


# --- dataset -------------------------------------------------------------------


def test_dev_split_has_at_least_1000_sentences():
    assert len(load("dev")) >= 1000


def test_every_type_and_language_present(records):
    types = {e["type"] for r in records for e in r["entities"]}
    assert types == TYPES
    assert {r["lang"] for r in records} == {"en", "hinglish", "hi"}
    assert any(not r["entities"] for r in records), "needs sentences with no PII"


def test_ids_unique(records):
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids))


def test_spans_in_bounds_and_non_overlapping(records):
    for r in records:
        spans = sorted((e["start"], e["end"]) for e in r["entities"])
        for start, end in spans:
            assert 0 <= start < end <= len(r["text"]), r["id"]
        for (_, end), (start, _) in zip(spans, spans[1:], strict=False):
            assert end <= start, r["id"]


def test_labelled_values_are_format_valid(records):
    for r in records:
        for e in r["entities"]:
            value = r["text"][e["start"] : e["end"]]
            assert value == value.strip(), r["id"]
            kind = e["type"]
            if kind == "AADHAAR":
                digits = "".join(c for c in value if c.isdigit())
                assert len(digits) == 12 and verhoeff.is_valid(digits), r["id"]
            elif kind == "PAN":
                assert len(value) == 10 and value[3].upper() in HOLDER_TYPES, r["id"]
            elif kind == "GSTIN":
                assert gstin_checksum.is_valid(value), r["id"]
            elif kind == "PHONE":
                digits = "".join(c for c in value if c.isdigit())[-10:]
                assert len(digits) == 10 and digits[0] in "6789", r["id"]
            elif kind == "EMAIL":
                assert value.count("@") == 1 and "." in value.split("@")[1], r["id"]
                assert value.isascii(), r["id"]
            elif kind == "UPI":
                assert value.count("@") == 1 and "." not in value.split("@")[1], r["id"]


def test_email_domains_are_reserved_or_fake(records):
    # Emails must never point at a real person's inbox.
    for r in records:
        for e in r["entities"]:
            if e["type"] == "EMAIL":
                domain = r["text"][e["start"] : e["end"]].split("@")[1]
                assert (
                    "example" in domain
                    or domain.endswith(".co.in")
                    or domain
                    in {
                        "paytm.com",
                        "okaxis.in",
                        "ybl.co",
                    }
                ), domain


def test_generator_is_deterministic():
    pytest.importorskip("faker")
    from benchmark.generators.build import build

    assert build(30, 1, 0.25) == build(30, 1, 0.25)


# --- metrics -------------------------------------------------------------------


def S(t, a, b):
    return Span(t, a, b)


def test_counts_math():
    c = Counts(tp=8, fp=2, fn=2)
    assert c.precision == 0.8 and c.recall == 0.8 and c.f1 == pytest.approx(0.8)
    assert Counts().precision is None and Counts().f1 is None


def test_strict_requires_type_and_exact_span():
    gold = [[S("PAN", 0, 10), S("PHONE", 20, 30)]]
    pred = [[S("PAN", 0, 10), S("BANK_ACCOUNT", 20, 30), S("PAN", 40, 50)]]
    c = strict_counts(gold, pred, ["PAN", "PHONE", "BANK_ACCOUNT"])
    assert (c["PAN"].tp, c["PAN"].fp, c["PAN"].fn) == (1, 1, 0)
    assert (c["PHONE"].tp, c["PHONE"].fn) == (0, 1)
    assert c["BANK_ACCOUNT"].fp == 1


def test_masked_counts_any_type_and_union_of_spans():
    gold = [[S("PHONE", 10, 20), S("PAN", 30, 40)]]
    pred = [[S("BANK_ACCOUNT", 10, 15), S("OTHER:DATE_TIME", 15, 20), S("PAN", 30, 39)]]
    assert masked_counts(gold, pred) == {"PHONE": [1, 1], "PAN": [0, 1]}


def test_false_alarms_ignore_unmapped_types():
    gold = [[S("PAN", 0, 10)]]
    pred = [[S("PAN", 0, 10), S("PHONE", 20, 30), S("OTHER:PERSON", 40, 50)]]
    assert false_alarms(gold, pred, ["PAN", "PHONE"]) == {"PAN": 0, "PHONE": 1}
