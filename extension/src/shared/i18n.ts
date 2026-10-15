import type { Translate } from "./summary.ts";

/** chrome.i18n lookup; falls back to the key so a missing string is visible, not blank. */
export const t: Translate = (key, substitutions) =>
  chrome.i18n.getMessage(key, substitutions) || key;
