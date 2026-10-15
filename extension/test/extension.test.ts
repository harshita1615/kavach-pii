import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { Kavach } from "../src/core/index.ts";
import { looksLikeSendButton, SITES, siteForHost } from "../src/shared/sites.ts";
import { merge } from "../src/shared/settings.ts";
import { countByType, summarize } from "../src/shared/summary.ts";

const root = new URL("../", import.meta.url);
const json = (path: string) => JSON.parse(readFileSync(new URL(path, root), "utf-8"));

// --- manifest: least privilege -----------------------------------------------------

const manifest = json("manifest.json");

test("manifest asks only for storage and the three chatbot sites", () => {
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.permissions, ["storage"]);
  assert.equal(manifest.host_permissions, undefined);
  assert.equal(manifest.optional_permissions, undefined);
  assert.equal(manifest.background, undefined);
  assert.equal(manifest.web_accessible_resources, undefined);
  assert.equal(manifest.externally_connectable, undefined);
  assert.equal(manifest.content_security_policy, undefined, "keep the strict MV3 default CSP");
  const matches = manifest.content_scripts.flatMap((c: { matches: string[] }) => c.matches);
  assert.deepEqual(matches.sort(), [
    "https://chatgpt.com/*",
    "https://claude.ai/*",
    "https://gemini.google.com/*",
  ]);
});

test("manifest version matches package.json", () => {
  assert.equal(manifest.version, json("package.json").version);
});

test("every site in sites.ts has a content-script match, and vice versa", () => {
  const matches = manifest.content_scripts[0].matches as string[];
  const hosts = matches.map((m) => new URL(m.replace("/*", "/")).hostname).sort();
  assert.deepEqual(SITES.flatMap((s) => s.hosts).sort(), hosts);
});

// --- locales ------------------------------------------------------------------------

const locales = readdirSync(new URL("_locales/", root));
const messages = Object.fromEntries(
  locales.map((l) => [l, json(`_locales/${l}/messages.json`) as Record<string, { message: string }>]),
);

test("English and Hindi have the same message keys", () => {
  assert.deepEqual(locales.sort(), ["en", "hi"]);
  assert.deepEqual(Object.keys(messages.hi!).sort(), Object.keys(messages.en!).sort());
});

test("store limits: name <= 75 and description <= 132 characters", () => {
  for (const [locale, m] of Object.entries(messages)) {
    assert.ok([...m.ext_name!.message].length <= 75, `${locale} name too long`);
    const description = m.ext_description!.message;
    assert.ok([...description].length <= 132, `${locale} description is ${[...description].length} chars`);
  }
});

test("every entity type has singular and plural names in every locale", () => {
  for (const m of Object.values(messages)) {
    for (const type of ["AADHAAR", "PAN", "UPI", "IFSC", "BANK_ACCOUNT", "PHONE", "GSTIN", "EMAIL"]) {
      assert.ok(m[`entity_${type}_one`] && m[`entity_${type}_other`], type);
    }
  }
});

// --- sites ---------------------------------------------------------------------------

test("siteForHost", () => {
  assert.equal(siteForHost("chatgpt.com")?.id, "chatgpt");
  assert.equal(siteForHost("CLAUDE.AI")?.id, "claude");
  assert.equal(siteForHost("gemini.google.com")?.id, "gemini");
  assert.equal(siteForHost("evilchatgpt.com"), undefined);
  assert.equal(siteForHost("google.com"), undefined);
});

test("generic send-button labels", () => {
  for (const label of ["Send message", "send-button", "Send prompt", "भेजें"]) {
    assert.ok(looksLikeSendButton(label), label);
  }
  for (const label of ["Sender settings", "Resend code", "Stop", ""]) {
    assert.ok(!looksLikeSendButton(label), label);
  }
});

// --- summary --------------------------------------------------------------------------

const en = (key: string) => messages.en![key]!.message;
const hi = (key: string) => messages.hi![key]!.message;

test("summary lists types in a fixed order with plurals, never values", () => {
  const text = "UPI rahul@okaxis, PAN ABCPE1234F, PAN AAAPZ9876K, mobile 9876543210";
  const counts = countByType(new Kavach().scan(text));
  const summary = summarize(counts, en);
  assert.equal(summary, "2 PANs, 1 UPI ID and 1 phone number");
  assert.equal(summarize(counts, hi), "2 पैन, 1 यूपीआई आईडी और 1 फ़ोन नंबर");
  for (const value of ["rahul@okaxis", "ABCPE1234F", "9876543210"]) {
    assert.ok(!summary.includes(value));
  }
});

test("summary of one type", () => {
  const counts = countByType(new Kavach().scan("PAN ABCPE1234F"));
  assert.equal(summarize(counts, en), "1 PAN");
});

// --- settings ---------------------------------------------------------------------------

test("settings merge fills defaults and ignores junk", () => {
  assert.deepEqual(merge(undefined).enabled, { chatgpt: true, claude: true, gemini: true });
  const s = merge({ enabled: { claude: false }, caught: { PAN: 3 } });
  assert.deepEqual(s.enabled, { chatgpt: true, claude: false, gemini: true });
  assert.deepEqual(s.caught, { PAN: 3 });
  assert.deepEqual(merge("nonsense").caught, {});
});
