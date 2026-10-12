/** Kavach detection core for the browser, ported from the Python package.
 *
 * Runs entirely in memory: no network, storage or logging. */

import { Engine } from "./engine.ts";
import { RULES } from "./rules.ts";
import { assertMode, MaskingSession, type Mode } from "./session.ts";
import type { Detection, EntityType } from "./types.ts";

export const SYSTEM_PROMPT: string = RULES.systemPrompt;

export class Kavach {
  readonly mode: Mode;
  readonly #engine: Engine;

  constructor(
    options: { entities?: Iterable<string> | null; mode?: Mode; threshold?: number } = {},
  ) {
    const mode = options.mode ?? "mask";
    assertMode(mode);
    this.mode = mode;
    this.#engine = new Engine(options.entities, options.threshold);
  }

  get entities(): ReadonlySet<EntityType> {
    return this.#engine.entities;
  }

  /** Detect only: type, position (UTF-16 offsets) and confidence. */
  scan(text: string): Detection[] {
    return this.#engine.analyze(text);
  }

  /** A new session in this instance's mode. */
  session(): MaskingSession {
    return new MaskingSession(this.#engine, this.mode);
  }

  /** Replace PII with placeholders permanently, whatever the mode. */
  redact(text: string): string {
    return new MaskingSession(this.#engine, "redact").mask(text);
  }
}

export { Engine, resolveOverlaps } from "./engine.ts";
export { MaskingSession, type Mode } from "./session.ts";
export { type Detection, ENTITY_TYPES, type EntityType } from "./types.ts";
