/** Detection pipeline, mirroring kavach/engine.py:
 * detect -> validate -> context score -> resolve overlaps. */

import { hasContext, hasNotPiiLabel } from "./context.ts";
import { ALL_DETECTORS } from "./detectors.ts";
import { RULES } from "./rules.ts";
import { type Detection, type Detector, type EntityType, ENTITY_TYPES, isEntityType } from "./types.ts";

const NUMERIC = new Set<EntityType>(RULES.numericEntities);
const SPECIFICITY_RANK = new Map<EntityType, number>(RULES.specificity.map((t, i) => [t, i]));

/** Python's round(x, 4) for the values the pipeline produces. */
function round4(x: number): number {
  return Math.round(x * 1e4) / 1e4;
}

export function parseEntities(entities?: Iterable<string> | null): ReadonlySet<EntityType> {
  if (entities == null) return new Set(ENTITY_TYPES);
  const parsed = new Set<EntityType>();
  for (const entity of entities) {
    const name = String(entity).toUpperCase();
    if (!isEntityType(name)) {
      throw new RangeError(
        `unknown entity ${JSON.stringify(entity)}; expected one of: ${ENTITY_TYPES.join(", ")}`,
      );
    }
    parsed.add(name);
  }
  return parsed;
}

/** Keep a non-overlapping subset, preferring higher score, then longer span,
 * then the more specific entity type. Returned in order of position. */
export function resolveOverlaps(detections: Iterable<Detection>): Detection[] {
  const ranked = [...detections].sort(
    (a, b) =>
      b.score - a.score ||
      b.end - b.start - (a.end - a.start) ||
      SPECIFICITY_RANK.get(a.entityType)! - SPECIFICITY_RANK.get(b.entityType)! ||
      a.start - b.start,
  );
  const kept: Detection[] = [];
  for (const candidate of ranked) {
    if (kept.every((k) => candidate.end <= k.start || candidate.start >= k.end)) {
      kept.push(candidate);
    }
  }
  return kept.sort((a, b) => a.start - b.start);
}

export class Engine {
  readonly entities: ReadonlySet<EntityType>;
  readonly threshold: number;
  readonly #detectors: Map<EntityType, Detector>;

  constructor(entities?: Iterable<string> | null, threshold: number = RULES.defaultThreshold) {
    if (!(threshold >= 0 && threshold <= 1)) {
      throw new RangeError(`threshold must be in [0, 1], got ${threshold}`);
    }
    this.entities = parseEntities(entities);
    this.threshold = threshold;
    this.#detectors = new Map(
      ALL_DETECTORS.filter((d) => this.entities.has(d.entityType)).map((d) => [d.entityType, d]),
    );
  }

  /** Detect all enabled entities in text. */
  analyze(text: string): Detection[] {
    if (!text) return [];
    const candidates: Detection[] = [];
    for (const detector of this.#detectors.values()) {
      for (const detection of detector.detect(text)) {
        const scored = this.#applyContext(text, detection, detector);
        if (scored.score >= this.threshold) candidates.push(scored);
      }
    }
    return resolveOverlaps(candidates);
  }

  /** Canonical form of a detected value, used to give repeats one placeholder. */
  normalize(detection: Detection, text: string): string {
    const detector = this.#detectors.get(detection.entityType)!;
    return detector.normalize(text.slice(detection.start, detection.end));
  }

  #applyContext(text: string, detection: Detection, detector: Detector): Detection {
    let score = detection.score;
    if (
      !detector.requiresContext &&
      hasContext(text, detection.start, detection.end, detection.entityType)
    ) {
      score += RULES.contextBoost;
    }
    if (NUMERIC.has(detection.entityType) && hasNotPiiLabel(text, detection.start)) {
      score -= RULES.notPiiLabelPenalty;
    }
    score = Math.min(1, Math.max(0, round4(score)));
    return score === detection.score ? detection : Object.freeze({ ...detection, score });
  }
}
