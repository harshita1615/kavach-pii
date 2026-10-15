/** Turn detections into a human summary ("1 Aadhaar number and 2 PANs").
 * Only types and counts: never the detected values. */

import type { Detection, EntityType } from "../core/index.ts";
import { ENTITY_TYPES } from "../core/index.ts";

export type Translate = (key: string, substitutions?: string[]) => string;

export function countByType(detections: readonly Detection[]): Map<EntityType, number> {
  const counts = new Map<EntityType, number>();
  for (const d of detections) counts.set(d.entityType, (counts.get(d.entityType) ?? 0) + 1);
  // Stable display order, independent of where items appear in the text.
  return new Map(ENTITY_TYPES.filter((t) => counts.has(t)).map((t) => [t, counts.get(t)!]));
}

export function summarize(counts: ReadonlyMap<EntityType, number>, t: Translate): string {
  const parts = [...counts].map(
    ([type, n]) => `${n} ${t(`entity_${type}_${n === 1 ? "one" : "other"}`)}`,
  );
  if (parts.length <= 1) return parts.join("");
  return `${parts.slice(0, -1).join(", ")} ${t("list_and")} ${parts.at(-1)}`;
}
