// Build the website demo into docs/demo/demo.js.
//
//   npm run build:demo
//
// The bundle is committed, so the website needs no build step; CI rebuilds it
// and fails if the committed copy is stale. Not minified, so visitors can read
// exactly what runs.

import * as esbuild from "esbuild-wasm";

const root = new URL("../", import.meta.url);

await esbuild.build({
  absWorkingDir: new URL(".", root).pathname.replace(/^\/([A-Za-z]:)/, "$1"),
  entryPoints: ["src/demo/demo.ts"],
  outfile: "../docs/demo/demo.js",
  bundle: true,
  format: "iife",
  // Regex lookbehind and private class fields need browsers from 2023 on.
  target: ["chrome109", "firefox115", "safari16.4"],
  charset: "utf8",
  legalComments: "none",
  logLevel: "warning",
  banner: {
    js: "// Generated from extension/src/demo/demo.ts by `npm run build:demo`. Do not edit.",
  },
});

console.log("built docs/demo/demo.js");
