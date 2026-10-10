"""Build the synthetic benchmark dataset.

    pip install -e ".[benchmark]"
    python -m benchmark.generators.build            # writes both splits to benchmark/dataset/

Deterministic for a given seed and Faker version. The generated file is
committed, so evaluation never needs Faker.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from importlib.metadata import version
from pathlib import Path

from faker import Faker

from benchmark.generators import ids
from benchmark.generators.templates import (
    HOLDOUT_NEGATIVE,
    HOLDOUT_POSITIVE,
    NEGATIVE,
    POSITIVE,
    Template,
)

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"

# split -> (positive templates, negative templates, default size, default seed, file)
SPLITS = {
    "dev": (POSITIVE, NEGATIVE, 1500, 2026, "kavach_bench_v1.jsonl"),
    "holdout": (HOLDOUT_POSITIVE, HOLDOUT_NEGATIVE, 600, 7, "kavach_bench_v1_holdout.jsonl"),
}

SLOT = re.compile(r"\{([A-Z0-9_]+)\}")

LABELS = {
    "AADHAAR": "AADHAAR",
    "PAN": "PAN",
    "UPI": "UPI",
    "IFSC": "IFSC",
    "BANK": "BANK_ACCOUNT",
    "PHONE": "PHONE",
    "GSTIN": "GSTIN",
    "EMAIL": "EMAIL",
    "EMAIL_UPILIKE": "EMAIL",
}

BANK_NAMES = ("SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Canara Bank", "Bank of Baroda")


class Filler:
    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.fake = Faker("en_IN")
        self.fake.seed_instance(seed)

    def _person(self) -> tuple[str, str]:
        return self.fake.first_name(), self.fake.last_name()

    def fill(self, slot: str) -> str:
        r = self.rng
        simple = {
            "AADHAAR": ids.aadhaar,
            "PAN": ids.pan,
            "IFSC": ids.ifsc,
            "BANK": ids.bank_account,
            "PHONE": ids.phone,
            "GSTIN": ids.gstin,
            "NEG_ORDER12": ids.order_id_12,
            "NEG_UTR": ids.utr,
            "NEG_TIMESTAMP": ids.timestamp,
            "NEG_INVOICE": ids.invoice,
            "NEG_BADPAN": ids.bad_pan,
            "NEG_BADAADHAAR": ids.bad_aadhaar,
            "NEG_ORDER10": ids.order_id_10,
            "NEG_PNR": ids.pnr,
            "NEG_PINCODE": ids.pincode,
            "NEG_AMOUNT": ids.amount,
            "NEG_TRACKING": ids.tracking,
            "NEG_CARD": ids.card_last4,
            "NEG_OTP": ids.otp,
            "NEG_TICKET": ids.ticket,
            "NEG_SMALL": ids.small_number,
        }
        if slot in simple:
            return simple[slot](r)
        if slot == "UPI":
            return ids.upi(r, *self._person())
        if slot == "EMAIL":
            return ids.email(r, *self._person())
        if slot == "EMAIL_UPILIKE":
            return ids.email_upi_like(r, *self._person())
        if slot == "NAME":
            return self.fake.name()
        if slot == "CITY":
            return self.fake.city()
        if slot == "DATE":
            return self.fake.date_between("-1y", "+1y").strftime(r.choice(("%d/%m/%Y", "%d %b %Y")))
        if slot == "BANKNAME":
            return r.choice(BANK_NAMES)
        raise KeyError(f"unknown slot {slot}")


def render(template: Template, filler: Filler) -> tuple[str, list[dict]]:
    parts: list[str] = []
    entities: list[dict] = []
    cursor = 0
    length = 0
    for match in SLOT.finditer(template.text):
        literal = template.text[cursor : match.start()]
        parts.append(literal)
        length += len(literal)
        slot = match.group(1)
        value = filler.fill(slot)
        if slot in LABELS:
            entities.append({"type": LABELS[slot], "start": length, "end": length + len(value)})
        parts.append(value)
        length += len(value)
        cursor = match.end()
    parts.append(template.text[cursor:])
    return "".join(parts), entities


def build(
    n: int,
    seed: int,
    negative_share: float,
    positive: list[Template] = POSITIVE,
    negative: list[Template] = NEGATIVE,
    prefix: str = "kb1",
) -> list[dict]:
    filler = Filler(seed)
    rng = random.Random(seed + 1)
    records = []
    for i in range(n):
        pool = negative if rng.random() < negative_share else positive
        template = rng.choice(pool)
        text, entities = render(template, filler)
        records.append(
            {
                "id": f"{prefix}-{i:05d}",
                "lang": template.lang,
                "scenario": template.scenario,
                "text": text,
                "entities": entities,
            }
        )
    return records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="all")
    parser.add_argument("--negative-share", type=float, default=0.25)
    args = parser.parse_args(argv)

    for split in SPLITS if args.split == "all" else [args.split]:
        positive, negative, n, seed, filename = SPLITS[split]
        prefix = "kb1" if split == "dev" else "kb1h"
        records = build(n, seed, args.negative_share, positive, negative, prefix)
        out = DATASET_DIR / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8", newline="\n") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        n_entities = sum(len(r["entities"]) for r in records)
        print(
            f"{split}: wrote {len(records)} sentences, {n_entities} entities to {out.name} "
            f"(seed {seed}, Faker {version('faker')})"
        )


if __name__ == "__main__":
    main()
