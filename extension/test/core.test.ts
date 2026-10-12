import assert from "node:assert/strict";
import { test } from "node:test";

import { Kavach, SYSTEM_PROMPT } from "../src/core/index.ts";
import {
  gstinCheckChar,
  gstinIsValid,
  verhoeffCheckDigit,
  verhoeffIsValid,
} from "../src/core/validators.ts";

const PAN = "ABCPE1234F";
const PAN_2 = "AAAPZ9876K";
const UPI = "rahul@okaxis";

test("verhoeff: reference vector and round trip", () => {
  assert.equal(verhoeffCheckDigit("236"), "3");
  assert.ok(verhoeffIsValid("2363"));
  assert.ok(!verhoeffIsValid("2364"));
  for (let i = 0; i < 200; i++) {
    const body = String(10_000_000_000 + i * 7919);
    assert.ok(verhoeffIsValid(body + verhoeffCheckDigit(body)));
  }
});

test("verhoeff: rejects non-digits without echoing input", () => {
  assert.throws(() => verhoeffIsValid("12a4"), (e: Error) => !e.message.includes("12a4"));
  assert.throws(() => verhoeffIsValid("२३४"));
});

test("gstin: published example", () => {
  assert.equal(gstinCheckChar("27AAPFU0939F1Z"), "V");
  assert.ok(gstinIsValid("27AAPFU0939F1ZV"));
  assert.ok(gstinIsValid("27aapfu0939f1zv"));
});

test("mask and unmask round trip", () => {
  const s = new Kavach().session();
  const masked = s.mask(`My PAN is ${PAN}, refund to ${UPI}. Verify ${PAN}.`);
  assert.equal(masked, "My PAN is [PAN_1], refund to [UPI_1]. Verify [PAN_1].");
  assert.equal(
    s.unmask("Refund for [PAN_1] sent to [UPI_1]"),
    `Refund for ${PAN} sent to ${UPI}`,
  );
});

test("mapping persists across messages; sessions are independent", () => {
  const k = new Kavach();
  const s1 = k.session();
  s1.mask(`PAN ${PAN}`);
  assert.equal(s1.mask(`new ${PAN_2}, old ${PAN}`), "new [PAN_2], old [PAN_1]");
  const s2 = k.session();
  assert.equal(s2.mask(PAN_2), "[PAN_1]");
});

test("unmask tolerates small edits and ignores unknown placeholders", () => {
  const s = new Kavach().session();
  s.mask(PAN);
  for (const variant of ["[pan_1]", "[ PAN_1 ]", "[PAN _ 1]", "[Pan_01]"]) {
    assert.equal(s.unmask(`ok ${variant}`), `ok ${PAN}`);
  }
  for (const text of ["[PAN_9]", "[PAN_]", "[PAN 1]", "PAN_1", "[PASSPORT_1]", "[PAN_१]"]) {
    assert.equal(s.unmask(text), text);
  }
});

test("existing placeholder text in the input is not reused", () => {
  const s = new Kavach().session();
  assert.equal(s.mask(`Earlier [pan_1]; PAN ${PAN}`), "Earlier [pan_1]; PAN [PAN_2]");
});

test("redact mode keeps no mapping", () => {
  const s = new Kavach({ mode: "redact" }).session();
  const masked = s.mask(`PAN ${PAN} and ${PAN_2}`);
  assert.equal(masked, "PAN [PAN_1] and [PAN_2]");
  assert.equal(s.unmask(masked), masked);
  assert.equal(new Kavach().redact(`PAN ${PAN}`), "PAN [PAN_1]");
});

test("scan mode leaves text unchanged and counts", () => {
  const s = new Kavach({ mode: "scan" }).session();
  assert.equal(s.mask(`${PAN} ${PAN} ${UPI}`), `${PAN} ${PAN} ${UPI}`);
  assert.deepEqual(s.counts, { PAN: 2, UPI: 1 });
});

test("toString and counts hold no values", () => {
  const s = new Kavach().session();
  s.mask(`PAN ${PAN} UPI ${UPI}`);
  for (const text of [String(s), JSON.stringify(s.counts)]) {
    assert.ok(!text.includes(PAN) && !text.includes(UPI));
  }
});

test("entity filter and validation", () => {
  assert.deepEqual(
    new Kavach({ entities: ["pan"] }).scan(`${PAN} ${UPI}`).map((d) => d.entityType),
    ["PAN"],
  );
  assert.throws(() => new Kavach({ entities: ["PASSPORT"] }), /unknown entity/);
  assert.throws(() => new Kavach({ threshold: 2 }), /threshold/);
  assert.throws(() => new Kavach({ mode: "encrypt" as never }), /mode/);
});

test("system prompt matches the Python package", () => {
  assert.match(SYSTEM_PROMPT, /\[PAN_1\]/);
});

test("long input is fast", () => {
  const text = "lorem ipsum 12345 ".repeat(5000) + `PAN ${PAN}`;
  const t0 = performance.now();
  assert.equal(new Kavach().scan(text).length, 1);
  assert.ok(performance.now() - t0 < 2000);
});
