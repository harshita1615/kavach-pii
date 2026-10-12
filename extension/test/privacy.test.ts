/** The detection core must never log, store or transmit anything. */

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

const CORE = new URL("../src/core/", import.meta.url);

const FORBIDDEN = [
  "console.",
  "fetch(",
  "XMLHttpRequest",
  "WebSocket",
  "sendBeacon",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "chrome.",
  "eval(",
  "new Function",
  "import(",
];

for (const file of readdirSync(CORE).filter((f) => f.endsWith(".ts"))) {
  test(`core/${file} has no logging, storage, network or dynamic code`, () => {
    const source = readFileSync(new URL(file, CORE), "utf-8");
    for (const token of FORBIDDEN) {
      assert.ok(!source.includes(token), `${file} contains ${token}`);
    }
  });
}
