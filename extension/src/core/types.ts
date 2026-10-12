/**
 * Core data structures, mirroring kavach/types.py.
 *
 * Privacy rule: a Detection never holds the matched text, only its position.
 */

export const ENTITY_TYPES = [
  "AADHAAR",
  "PAN",
  "UPI",
  "IFSC",
  "BANK_ACCOUNT",
  "PHONE",
  "GSTIN",
  "EMAIL",
] as const;

export type EntityType = (typeof ENTITY_TYPES)[number];

export function isEntityType(value: string): value is EntityType {
  return (ENTITY_TYPES as readonly string[]).includes(value);
}

/** One detected entity: the span text.slice(start, end). Offsets are UTF-16 code units. */
export interface Detection {
  readonly entityType: EntityType;
  readonly start: number;
  readonly end: number;
  readonly score: number;
  readonly detector: string;
}

export function makeDetection(
  entityType: EntityType,
  start: number,
  end: number,
  score: number,
  detector: string,
): Detection {
  if (!(start >= 0 && start < end)) {
    throw new RangeError(`invalid span: start=${start}, end=${end}`);
  }
  if (!(score >= 0 && score <= 1)) {
    throw new RangeError(`score must be in [0, 1], got ${score}`);
  }
  return Object.freeze({ entityType, start, end, score, detector });
}

/** Finds candidate spans of one entity type and keeps only those that validate. */
export interface Detector {
  readonly entityType: EntityType;
  readonly name: string;
  /** If true, the pipeline does not add the context boost a second time. */
  readonly requiresContext: boolean;
  detect(text: string): Detection[];
  /** Canonical form, so formatting variants of one value share a placeholder. */
  normalize(value: string): string;
}
