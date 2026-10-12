/** Context words, mirroring kavach/context/scorer.py. */

import { RULES } from "./rules.ts";
import { escapeRegex, isAscii, WS } from "./regex.ts";
import type { EntityType } from "./types.ts";

const keywordPatterns = new Map<EntityType, RegExp>();

function keywordPattern(entityType: EntityType): RegExp {
  let pattern = keywordPatterns.get(entityType);
  if (!pattern) {
    const words = [...new Set(RULES.keywords[entityType])].sort((a, b) => b.length - a.length);
    const parts = words.map((word) =>
      isAscii(word) ? `(?<![a-z0-9])${escapeRegex(word)}(?![a-z0-9])` : escapeRegex(word),
    );
    pattern = new RegExp(parts.join("|"), "iu");
    keywordPatterns.set(entityType, pattern);
  }
  return pattern;
}

/** True if a context word for entityType appears within the window around
 * text.slice(start, end). The span itself is not searched. */
export function hasContext(
  text: string,
  start: number,
  end: number,
  entityType: EntityType,
  before = RULES.contextWindowBefore,
  after = RULES.contextWindowAfter,
): boolean {
  const pattern = keywordPattern(entityType);
  const left = text.slice(Math.max(0, start - before), start);
  const right = text.slice(end, end + after);
  // Searched separately so a keyword can't be formed across the span.
  return pattern.test(left) || pattern.test(right);
}

function alternation(words: string[]): string {
  return [...new Set(words)]
    .sort((a, b) => b.length - a.length)
    .map((word) => {
      const escaped = word.trim().split(/ +/).map(escapeRegex).join(`${WS}+`);
      return isAscii(word) ? `(?<![a-z0-9])${escaped}` : escaped;
    })
    .join("|");
}

// A not-PII label, an optional "no./number/id/#", an optional "is/hai/was",
// optional punctuation, then the span. Must end exactly where the span starts.
const NOT_PII_LABEL = new RegExp(
  `(?:${alternation(RULES.notPiiLabels)})` +
    `(?:${WS}*(?:no\\.?|number|num|id|#))?` +
    `(?:${WS}+(?:is|hai|was))?` +
    `${WS}*[:#.\\-]?${WS}*$`,
  "iu",
);

/** True if the span starting at `start` is directly preceded by a label such
 * as "Order no." or "UTR", which says the value is not personal data. */
export function hasNotPiiLabel(text: string, start: number): boolean {
  return NOT_PII_LABEL.test(text.slice(Math.max(0, start - RULES.labelWindow), start));
}
