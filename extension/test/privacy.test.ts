/** No part of the extension may log, transmit or run remote code. The
 * detection core may not even touch browser storage or extension APIs. */

import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { test } from "node:test";

const SRC = new URL("../src/", import.meta.url);

const EVERYWHERE = [
  "console.",
  "fetch(",
  "XMLHttpRequest",
  "WebSocket",
  "EventSource",
  "sendBeacon",
  "eval(",
  "new Function",
  "import(",
  "chrome.runtime.sendMessage",
  "chrome.tabs",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "document.cookie",
];
const CORE_ONLY = ["chrome."];
// A URL inside a string literal could be fetched or loaded; URLs in comments are fine.
const URL_STRING = /["'`]\s*(?:https?:)?\/\//;

function files(dir: URL, prefix = ""): { path: string; url: URL }[] {
  return readdirSync(dir).flatMap((name) => {
    const url = new URL(name, dir);
    return statSync(url).isDirectory()
      ? files(new URL(`${name}/`, dir), `${prefix}${name}/`)
      : [{ path: `${prefix}${name}`, url }];
  });
}

for (const file of files(SRC).filter((f) => /\.(ts|html)$/.test(f.path))) {
  test(`${file.path}: no logging, network, remote code or extra storage`, () => {
    const source = readFileSync(file.url, "utf-8");
    const forbidden = file.path.startsWith("core/") ? [...EVERYWHERE, ...CORE_ONLY] : EVERYWHERE;
    for (const token of forbidden) {
      assert.ok(!source.includes(token), `${file.path} contains ${token}`);
    }
    assert.doesNotMatch(source, URL_STRING, `${file.path} contains a URL string`);
  });
}
