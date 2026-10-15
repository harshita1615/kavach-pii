/**
 * Settings and counters in chrome.storage.local.
 *
 * Stored: an on/off flag per site, and how many items of each type were
 * caught. Never any text, value or URL.
 */

import type { EntityType } from "../core/index.ts";
import { SITES, type Site } from "./sites.ts";

export interface Settings {
  enabled: Record<Site["id"], boolean>;
  caught: Partial<Record<EntityType, number>>;
}

const KEY = "kavach";

export function defaults(): Settings {
  return {
    enabled: Object.fromEntries(SITES.map((s) => [s.id, true])) as Settings["enabled"],
    caught: {},
  };
}

export function merge(stored: unknown): Settings {
  const base = defaults();
  if (!stored || typeof stored !== "object") return base;
  const s = stored as Partial<Settings>;
  return {
    enabled: { ...base.enabled, ...(s.enabled ?? {}) },
    caught: { ...(s.caught ?? {}) },
  };
}

export async function load(): Promise<Settings> {
  const data = await chrome.storage.local.get(KEY);
  return merge(data[KEY]);
}

export async function save(settings: Settings): Promise<void> {
  await chrome.storage.local.set({ [KEY]: settings });
}

export async function addCaught(counts: ReadonlyMap<EntityType, number>): Promise<void> {
  const settings = await load();
  for (const [type, n] of counts) settings.caught[type] = (settings.caught[type] ?? 0) + n;
  await save(settings);
}

export function onChange(listener: (settings: Settings) => void): void {
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && KEY in changes) listener(merge(changes[KEY]!.newValue));
  });
}
