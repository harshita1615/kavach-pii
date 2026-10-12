/**
 * Regex building blocks that reproduce Python `re` semantics in JavaScript.
 *
 * The Python package is the reference implementation. Where the two engines
 * differ, these constants make JavaScript behave like Python:
 *   - Python's `\w` (str patterns) is Unicode-aware; JavaScript's is ASCII-only.
 *   - Python's `\s` includes \x1c-\x1f and \x85 but not ﻿; JavaScript's is the reverse.
 * Patterns use [0-9] rather than \d, and avoid \b, in both languages.
 * All patterns are compiled with the `u` flag.
 */

/** Characters of Python's `\w`, for use inside a character class. */
export const W_CHARS = String.raw`\p{L}\p{N}_`;

/** Python's `\w`. */
export const W = `[${W_CHARS}]`;

/** Python's `\s`. */
export const WS = String.raw`[\t\n\v\f\r \x1c-\x1f\x85\xa0  -     　]`;

/** Escape a literal for use in a `u`-flag pattern (outside a character class). */
export function escapeRegex(literal: string): string {
  return literal.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function isAscii(value: string): boolean {
  return /^[\x00-\x7f]*$/.test(value);
}
