"""Span-level metrics.

strict:   a prediction counts only if type, start and end all match a gold span.
masked:   a gold span counts as masked if predictions of ANY type cover all of
          it. This is what matters for privacy: a phone number masked as
          BANK_ACCOUNT still never reaches the LLM.
false alarms: predictions (of a benchmark entity type) that overlap no gold span.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    type: str
    start: int
    end: int

    def overlaps(self, other: Span) -> bool:
        return self.start < other.end and other.start < self.end


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float | None:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else None

    @property
    def recall(self) -> float | None:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return 2 * p * r / (p + r)


def strict_counts(
    gold: list[list[Span]], pred: list[list[Span]], types: list[str]
) -> dict[str, Counts]:
    counts = {t: Counts() for t in types}
    for g_doc, p_doc in zip(gold, pred, strict=True):
        g_set = {s for s in g_doc if s.type in counts}
        p_set = {s for s in p_doc if s.type in counts}
        for s in g_set & p_set:
            counts[s.type].tp += 1
        for s in p_set - g_set:
            counts[s.type].fp += 1
        for s in g_set - p_set:
            counts[s.type].fn += 1
    return counts


def _covered(span: Span, preds: list[Span]) -> bool:
    """True if the union of preds covers every character of span."""
    position = span.start
    for p in sorted(preds, key=lambda s: s.start):
        if p.start > position:
            break
        position = max(position, p.end)
        if position >= span.end:
            return True
    return position >= span.end


def masked_counts(gold: list[list[Span]], pred: list[list[Span]]) -> dict[str, list[int]]:
    """{type: [masked, total]} over gold spans, using predictions of any type."""
    result: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for g_doc, p_doc in zip(gold, pred, strict=True):
        for span in g_doc:
            result[span.type][1] += 1
            if _covered(span, p_doc):
                result[span.type][0] += 1
    return dict(result)


def false_alarms(
    gold: list[list[Span]], pred: list[list[Span]], types: list[str]
) -> dict[str, int]:
    """Predictions of a benchmark type that overlap no gold span at all."""
    result = dict.fromkeys(types, 0)
    for g_doc, p_doc in zip(gold, pred, strict=True):
        for p in p_doc:
            if p.type in result and not any(p.overlaps(g) for g in g_doc):
                result[p.type] += 1
    return result
