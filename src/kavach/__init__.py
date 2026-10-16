"""Kavach: detect, mask and restore Indian PII before it reaches an LLM."""

from kavach.kavach import SYSTEM_PROMPT, Kavach
from kavach.masking import MaskingSession, StreamUnmasker
from kavach.types import Detection, EntityType

__all__ = [
    "SYSTEM_PROMPT",
    "Detection",
    "EntityType",
    "Kavach",
    "MaskingSession",
    "StreamUnmasker",
]
__version__ = "0.2.0"
