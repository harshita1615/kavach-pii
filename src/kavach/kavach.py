"""Public entry point."""

from __future__ import annotations

from collections.abc import Iterable

from kavach.engine import DEFAULT_THRESHOLD, Engine
from kavach.masking.session import MODES, MaskingSession, Mode
from kavach.types import Detection, EntityType

SYSTEM_PROMPT = (
    "Some values in the user's message have been replaced with placeholders such as "
    "[PAN_1] or [PHONE_2]. Keep every placeholder exactly as written, including the "
    "brackets, capital letters and number. Do not guess the original values."
)


class Kavach:
    """Detect, mask and restore Indian PII.

    >>> k = Kavach(entities=["PAN", "UPI"])
    >>> session = k.session()
    >>> session.mask("PAN ABCPE1234F")
    'PAN [PAN_1]'
    """

    def __init__(
        self,
        entities: Iterable[EntityType | str] | None = None,
        mode: Mode = "mask",
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}; got {mode!r}")
        self.mode = mode
        self._engine = Engine(entities, threshold)

    @property
    def entities(self) -> frozenset[EntityType]:
        return self._engine.entities

    def scan(self, text: str) -> list[Detection]:
        """Detect only. Each Detection gives type, position and confidence;
        call detection.text_in(text) to read the value."""
        return self._engine.analyze(text)

    def session(self) -> MaskingSession:
        """A new session in this instance's mode. Use one per conversation."""
        return MaskingSession(self._engine, self.mode)

    def redact(self, text: str) -> str:
        """Replace PII with placeholders permanently, whatever the mode."""
        return MaskingSession(self._engine, "redact").mask(text)

    def __repr__(self) -> str:
        names = ",".join(sorted(e.value for e in self.entities))
        return f"<Kavach mode={self.mode} entities={names}>"
