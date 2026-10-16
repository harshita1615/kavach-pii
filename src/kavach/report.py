"""Scan reports shared by the CLI and the MCP server.

A report gives entity types, positions, scores and counts, never the values.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from kavach.types import Detection


def line_col(text: str, index: int) -> tuple[int, int]:
    """1-based line and column of text[index]."""
    line = text.count("\n", 0, index) + 1
    column = index - (text.rfind("\n", 0, index) + 1) + 1
    return line, column


def build(text: str, detections: list[Detection]) -> dict[str, Any]:
    items = []
    for d in detections:
        line, column = line_col(text, d.start)
        items.append(
            {
                "type": d.entity_type.value,
                "line": line,
                "column": column,
                "start": d.start,
                "end": d.end,
                "score": d.score,
            }
        )
    counts = Counter(d.entity_type.value for d in detections)
    return {"count": len(detections), "counts": dict(counts), "items": items}
