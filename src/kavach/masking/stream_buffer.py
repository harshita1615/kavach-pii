"""Unmasking for streamed LLM output.

A placeholder can be split across chunks ("[PA" + "N_1] is"). The buffer holds
back a trailing fragment that could still become a placeholder, and releases it
once it is closed, turns out not to be a placeholder, or grows too long.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from kavach.masking import placeholders

# Characters that can appear inside a (possibly LLM-mangled) placeholder.
_FRAGMENT = re.compile(r"\[[A-Za-z0-9_ \t]*")


class StreamUnmasker:
    def __init__(self, unmask: Callable[[str], str]) -> None:
        self._unmask = unmask
        self._pending = ""

    def feed(self, chunk: str) -> str:
        """Add a chunk; return the text that is safe to emit now, unmasked."""
        self._pending += chunk
        cut = self._hold_from(self._pending)
        ready, self._pending = self._pending[:cut], self._pending[cut:]
        return self._unmask(ready)

    def flush(self) -> str:
        """Emit everything still held. Call once when the stream ends."""
        ready, self._pending = self._pending, ""
        return self._unmask(ready)

    @staticmethod
    def _hold_from(text: str) -> int:
        """Index where a possible unfinished placeholder starts, or len(text)."""
        start = text.rfind("[")
        if start == -1:
            return len(text)
        tail = text[start:]
        if len(tail) <= placeholders.MAX_LENGTH and _FRAGMENT.fullmatch(tail):
            return start
        return len(text)

    def __repr__(self) -> str:
        return f"<StreamUnmasker pending_chars={len(self._pending)}>"
