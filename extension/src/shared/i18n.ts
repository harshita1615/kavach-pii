import type { Translate } from "./summary.ts";

/**
 * chrome.i18n lookup. Falls back to the key, so a missing string is visible
 * rather than blank, and never throws: after the extension is reloaded, an
 * orphaned content script's chrome.* calls throw "Extension context invalidated".
 */
export const t: Translate = (key, substitutions) => {
  try {
    return chrome.i18n.getMessage(key, substitutions) || key;
  } catch {
    return key;
  }
};
