"""Evaluate Kavach (and optionally default Presidio) on the synthetic benchmark.

    python -m benchmark.run_eval                 # Kavach only, both splits
    python -m benchmark.run_eval --presidio      # also Presidio (default + Indian recognizers)

The Presidio comparison needs: pip install -e ".[benchmark]"
                               python -m spacy download en_core_web_lg

Writes benchmark/results/<split>/results.md and results.json. Every number in
them is measured by this script; nothing is filled in by hand.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import random
import statistics
import time
from collections import defaultdict
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from benchmark.metrics import Span, false_alarms, masked_counts, strict_counts
from kavach import Kavach
from kavach.masking import placeholders

ROOT = Path(__file__).resolve().parent

# dev: the split Kavach was tuned on. holdout: written later, never tuned on.
SPLITS = {
    "dev": (ROOT / "dataset" / "kavach_bench_v1.jsonl", ROOT / "results" / "dev"),
    "holdout": (ROOT / "dataset" / "kavach_bench_v1_holdout.jsonl", ROOT / "results" / "holdout"),
}

TYPES = ["AADHAAR", "PAN", "UPI", "IFSC", "BANK_ACCOUNT", "PHONE", "GSTIN", "EMAIL"]

# Presidio entity types that correspond to a benchmark type.
PRESIDIO_MAP = {
    "IN_AADHAAR": "AADHAAR",
    "IN_PAN": "PAN",
    "IN_GSTIN": "GSTIN",
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
}

Predictor = Callable[[str], list[Span]]


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def gold_spans(records: list[dict]) -> list[list[Span]]:
    return [[Span(e["type"], e["start"], e["end"]) for e in r["entities"]] for r in records]


def kavach_predictor() -> Predictor:
    k = Kavach()

    def predict(text: str) -> list[Span]:
        return [Span(d.entity_type.value, d.start, d.end) for d in k.scan(text)]

    return predict


def presidio_predictor(with_india: bool) -> tuple[Predictor, list[str]]:
    """Default Presidio (spaCy en_core_web_lg, default recognizers), optionally
    with Presidio's own Indian recognizers added. These ship with Presidio but
    are not enabled in its default English configuration."""
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer import predefined_recognizers as pr

    analyzer = AnalyzerEngine()
    if with_india:
        for cls in (
            pr.InAadhaarRecognizer,
            pr.InPanRecognizer,
            pr.InGstinRecognizer,
            pr.InPassportRecognizer,
            pr.InVoterRecognizer,
            pr.InVehicleRegistrationRecognizer,
        ):
            analyzer.registry.add_recognizer(cls())
    supported = set(analyzer.get_supported_entities("en"))
    covers = [t for p, t in PRESIDIO_MAP.items() if p in supported]

    def predict(text: str) -> list[Span]:
        return [
            Span(PRESIDIO_MAP.get(r.entity_type, f"OTHER:{r.entity_type}"), r.start, r.end)
            for r in analyzer.analyze(text=text, language="en")
        ]

    return predict, covers


def latency_ms_per_1k_chars(predict: Predictor, texts: list[str], repeats: int) -> float:
    chars = sum(len(t) for t in texts)
    runs = []
    for _ in range(repeats):
        start = time.perf_counter()
        for text in texts:
            predict(text)
        runs.append(time.perf_counter() - start)
    return statistics.median(runs) * 1000 / chars * 1000


def evaluate(
    name: str, predict: Predictor, records: list[dict], repeats: int, covers: list[str]
) -> dict:
    gold = gold_spans(records)
    pred = [predict(r["text"]) for r in records]

    strict = strict_counts(gold, pred, TYPES)
    masked = masked_counts(gold, pred)
    alarms = false_alarms(gold, pred, TYPES)

    by_lang: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for record, g_doc, p_doc in zip(records, gold, pred, strict=True):
        m = masked_counts([g_doc], [p_doc])
        for covered, total in m.values():
            by_lang[record["lang"]][0] += covered
            by_lang[record["lang"]][1] += total

    clean = [(g, p) for g, p in zip(gold, pred, strict=True) if not g]
    flagged_clean = sum(1 for _, p in clean if any(s.type in TYPES for s in p))

    total_masked = sum(m[0] for m in masked.values())
    total_gold = sum(m[1] for m in masked.values())

    def untyped(docs: list[list[Span]]) -> list[list[Span]]:
        return [[Span("ALL", s.start, s.end) for s in d if s.type in TYPES] for d in docs]

    micro = strict_counts(untyped(gold), untyped(pred), ["ALL"])["ALL"]

    return {
        "name": name,
        "covers": covers,
        "per_entity": {
            t: {
                "precision": strict[t].precision,
                "recall": strict[t].recall,
                "f1": strict[t].f1,
                "tp": strict[t].tp,
                "fp": strict[t].fp,
                "fn": strict[t].fn,
                "masked": masked.get(t, [0, 0])[0],
                "gold": masked.get(t, [0, 0])[1],
                "false_alarms": alarms[t],
            }
            for t in TYPES
        },
        "overall": {
            "masked_recall": total_masked / total_gold if total_gold else None,
            "span_precision_untyped": micro.precision,
            "span_recall_untyped": micro.recall,
            "clean_sentences": len(clean),
            "clean_sentences_flagged": flagged_clean,
        },
        "masked_recall_by_lang": {
            lang: covered / total for lang, (covered, total) in sorted(by_lang.items()) if total
        },
        "latency_ms_per_1k_chars": latency_ms_per_1k_chars(
            predict, [r["text"] for r in records], repeats
        ),
    }


def round_trip(records: list[dict], seed: int = 0) -> dict:
    """mask -> simulated LLM reply -> unmask, per reply style."""
    k = Kavach()
    rng = random.Random(seed)
    styles = ["echo", "reordered", "case_and_spacing", "streamed", "brackets_dropped"]
    ok = dict.fromkeys(styles, 0)
    total = 0
    for record in records:
        text = record["text"]
        session = k.session()
        masked = session.mask(text)
        found = [m.group(0) for m in placeholders.PATTERN.finditer(masked)]
        if not found:
            continue
        total += 1
        first_value: dict[str, str] = {}
        for ph, d in zip(found, k.scan(text), strict=True):
            first_value.setdefault(ph, d.text_in(text))
        unique = list(dict.fromkeys(found))

        echo, expected = f"Noted: {masked}", f"Noted: {text}"
        ok["echo"] += session.unmask(echo) == expected

        reply = "Recorded " + "; ".join(reversed(unique))
        ok["reordered"] += session.unmask(reply) == "Recorded " + "; ".join(
            first_value[p] for p in reversed(unique)
        )

        drift = placeholders.PATTERN.sub(lambda m: f"[ {m.group(1).lower()}_{m.group(2)} ]", echo)
        ok["case_and_spacing"] += session.unmask(drift) == expected

        stream = session.stream()
        pieces, i = [], 0
        while i < len(echo):
            step = rng.randint(1, 8)
            pieces.append(stream.feed(echo[i : i + step]))
            i += step
        ok["streamed"] += "".join(pieces) + stream.flush() == expected

        dropped = placeholders.PATTERN.sub(lambda m: f"{m.group(1)}_{m.group(2)}", echo)
        ok["brackets_dropped"] += session.unmask(dropped) == expected
    return {"sentences": total, **{s: ok[s] / total if total else None for s in styles}}


# --- reporting -----------------------------------------------------------------


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"


def to_markdown(meta: dict, results: list[dict], rt: dict) -> str:
    split_note = {
        "dev": "**Dev split**: Kavach's rules were tuned on these templates, so these numbers "
        "are optimistic. See the holdout split for an unbiased estimate.",
        "holdout": "**Holdout split**: templates written after tuning and never used to tune "
        "Kavach. These are the numbers to quote.",
    }.get(meta.get("split", ""), "")
    lines = [
        f"# Kavach benchmark results: {meta.get('split', 'custom')} split",
        "",
        split_note,
        "",
        f"Dataset: `{meta['dataset']}`: {meta['sentences']} sentences, "
        f"{meta['gold_entities']} labelled entities, {meta['clean_sentences']} with no PII. "
        "Fully synthetic.",
        f"Run: {meta['date']} · Python {meta['python']} · kavach {meta['kavach']}"
        + (f" · presidio-analyzer {meta['presidio']}" if meta.get("presidio") else ""),
        "",
        "Generated by `python -m benchmark.run_eval`. Do not edit by hand.",
        "",
        "## Per entity (strict: exact type and span)",
        "",
    ]
    header = "| Entity | Gold | Kavach precision | Kavach recall | Kavach F1 | Kavach masked |"
    sep = "| --- | ---: | ---: | ---: | ---: | ---: |"
    kav, others = results[0], results[1:]
    for other in others:
        header += f" {other['name']} recall | {other['name']} masked |"
        sep += " ---: | ---: |"
    lines += [header, sep]
    for t in TYPES:
        e = kav["per_entity"][t]
        masked = e["masked"] / e["gold"] if e["gold"] else None
        row = (
            f"| {t} | {e['gold']} | {pct(e['precision'])} | {pct(e['recall'])} | "
            f"{pct(e['f1'])} | {pct(masked)} |"
        )
        for other in others:
            p = other["per_entity"][t]
            p_masked = p["masked"] / p["gold"] if p["gold"] else None
            p_recall = pct(p["recall"]) if t in other["covers"] else "no recognizer"
            row += f" {p_recall} | {pct(p_masked)} |"
        lines.append(row)

    lines += [
        "",
        "*Masked*: the value was fully covered by a detection of any type, so it would not "
        "reach the LLM. For Presidio this counts every Presidio entity type, including ones "
        "unrelated to the label (for example a phone number detected as DATE_TIME).",
        "",
        "## Overall",
        "",
        "| Metric | " + " | ".join(r["name"] for r in results) + " |",
        "| --- | " + " | ".join("---:" for _ in results) + " |",
    ]

    def row(label, fn):
        lines.append(f"| {label} | " + " | ".join(fn(r) for r in results) + " |")

    row("Masked recall (all entities)", lambda r: pct(r["overall"]["masked_recall"]))
    row("Span precision, type ignored", lambda r: pct(r["overall"]["span_precision_untyped"]))
    row(
        "Clean sentences wrongly flagged",
        lambda r: f"{r['overall']['clean_sentences_flagged']} / {r['overall']['clean_sentences']}",
    )
    row(
        "False alarms (no gold overlap)",
        lambda r: str(sum(r["per_entity"][t]["false_alarms"] for t in TYPES)),
    )
    row("Latency, ms per 1,000 chars", lambda r: f"{r['latency_ms_per_1k_chars']:.3f}")
    for lang in kav["masked_recall_by_lang"]:
        row(
            f"Masked recall, {lang}", lambda r, lang=lang: pct(r["masked_recall_by_lang"].get(lang))
        )

    lines += [
        "",
        "## False alarms by type (Kavach)",
        "",
        "| Entity | False alarms |",
        "| --- | ---: |",
    ]
    lines += [f"| {t} | {kav['per_entity'][t]['false_alarms']} |" for t in TYPES]

    lines += [
        "",
        "## Round trip (mask, simulated LLM reply, unmask)",
        "",
        f"Over {rt['sentences']} sentences where Kavach masked something.",
        "",
        "| Reply style | Fully restored |",
        "| --- | ---: |",
        f"| Echoed unchanged | {pct(rt['echo'])} |",
        f"| Placeholders reordered | {pct(rt['reordered'])} |",
        f"| Lowercased, spaces inside brackets | {pct(rt['case_and_spacing'])} |",
        f"| Streamed in 1-8 character chunks | {pct(rt['streamed'])} |",
        f"| Brackets dropped (`PAN_1`) | {pct(rt['brackets_dropped'])} |",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate Kavach on the synthetic benchmark.")
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="all")
    parser.add_argument(
        "--presidio",
        action="store_true",
        help="also evaluate Presidio, default and with its Indian recognizers enabled",
    )
    parser.add_argument("--repeats", type=int, default=5, help="timing repeats (median)")
    args = parser.parse_args(argv)
    for split in SPLITS if args.split == "all" else [args.split]:
        run(split, args.presidio, args.repeats)


def run(split: str, presidio: bool, repeats: int) -> None:
    dataset, out = SPLITS[split]
    records = load(dataset)
    results = [evaluate("kavach", kavach_predictor(), records, repeats, TYPES)]
    meta = {
        "split": split,
        "dataset": dataset.name,
        "sentences": len(records),
        "gold_entities": sum(len(r["entities"]) for r in records),
        "clean_sentences": sum(1 for r in records if not r["entities"]),
        "date": dt.date.today().isoformat(),
        "python": platform.python_version(),
        "kavach": version("kavach-pii"),
    }
    if presidio:
        try:
            meta["presidio"] = version("presidio-analyzer")
        except PackageNotFoundError:
            raise SystemExit(
                "presidio-analyzer is not installed: pip install -e '.[benchmark]'"
            ) from None
        for name, with_india in (("presidio-default", False), ("presidio+india", True)):
            predict, covers = presidio_predictor(with_india)
            results.append(evaluate(name, predict, records, 1, covers))
    rt = round_trip(records)

    out.mkdir(parents=True, exist_ok=True)
    markdown = to_markdown(meta, results, rt)
    (out / "results.md").write_text(markdown, encoding="utf-8")
    (out / "results.json").write_text(
        json.dumps({"meta": meta, "results": results, "round_trip": rt}, indent=2), encoding="utf-8"
    )
    print(markdown)


if __name__ == "__main__":
    main()
