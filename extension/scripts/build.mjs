// Build the extension into dist/.
//
//   npm run build
//
// Bundles the content script and popup with esbuild-wasm (WebAssembly, no
// native binary) and copies the static files. Output is not minified, so the
// published code stays readable for Chrome Web Store review and for users.

import { cpSync, mkdirSync, readFileSync, rmSync } from "node:fs";
import * as esbuild from "esbuild-wasm";

const root = new URL("../", import.meta.url);
const dist = new URL("dist/", root);

const manifest = JSON.parse(readFileSync(new URL("manifest.json", root), "utf-8"));
const pkg = JSON.parse(readFileSync(new URL("package.json", root), "utf-8"));
if (manifest.version !== pkg.version) {
  throw new Error(`manifest.json version ${manifest.version} != package.json ${pkg.version}`);
}

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

await esbuild.build({
  absWorkingDir: new URL(".", root).pathname.replace(/^\/([A-Za-z]:)/, "$1"),
  entryPoints: { content: "src/content/index.ts", popup: "src/popup/popup.ts" },
  outdir: "dist",
  bundle: true,
  format: "iife",
  target: "chrome120",
  charset: "utf8",
  legalComments: "none",
  logLevel: "warning",
});

for (const [from, to] of [
  ["manifest.json", "manifest.json"],
  ["src/popup/popup.html", "popup.html"],
  ["src/popup/popup.css", "popup.css"],
  ["icons", "icons"],
  ["_locales", "_locales"],
]) {
  cpSync(new URL(from, root), new URL(to, dist), { recursive: true });
}

console.log(`built kavach extension ${manifest.version} into dist/`);
