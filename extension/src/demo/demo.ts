/** Web demo for kavach.bigforge.tech/demo/: the extension's detection core,
 * run on whatever the visitor types. Everything stays in the page; the site's
 * Content-Security-Policy blocks network requests as well. */

import { Kavach } from "../core/index.ts";
import type { MaskingSession } from "../core/session.ts";
import { ENTITY_TYPES, type EntityType } from "../core/types.ts";

const LABELS: Record<EntityType, string> = {
  AADHAAR: "Aadhaar",
  PAN: "PAN",
  UPI: "UPI ID",
  IFSC: "IFSC",
  BANK_ACCOUNT: "Bank account",
  PHONE: "Phone",
  GSTIN: "GSTIN",
  EMAIL: "Email",
};

// Made-up values only: format-valid (correct check digits) but belonging to no one.
const SAMPLES: Record<string, string> = {
  english:
    "Hi, my PAN is ABCPE1234F and Aadhaar 2345 6789 0124. Please send the refund to " +
    "rahul@okaxis or call +91 98765 43210. Email: rahul@example.com",
  hinglish:
    "Mera khata number 30012345678 hai, IFSC SBIN0001234. UPI pe bhejo: 9876543210@paytm. " +
    "Order no. 4029381123 ka status batao.",
  hindi:
    "मेरा आधार 2345 6789 0124 है और मोबाइल 98765 43210 है। GSTIN 27ABCPE1234F1ZB वाले बिल " +
    "की कॉपी भेजें।",
};

function byId<T extends HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`#${id} missing`);
  return el as T;
}

const input = byId<HTMLTextAreaElement>("input");
const highlighted = byId<HTMLElement>("highlighted");
const counts = byId<HTMLElement>("counts");
const masked = byId<HTMLElement>("masked");
const copy = byId<HTMLButtonElement>("copy");
const reply = byId<HTMLTextAreaElement>("reply");
const restored = byId<HTMLElement>("restored");
const entityBoxes = byId<HTMLElement>("entities");

let kavach = new Kavach();
let session: MaskingSession = kavach.session();
let replyEdited = false;

for (const type of ENTITY_TYPES) {
  const label = document.createElement("label");
  const box = document.createElement("input");
  box.type = "checkbox";
  box.value = type;
  box.checked = true;
  box.addEventListener("change", () => {
    const chosen = [...entityBoxes.querySelectorAll<HTMLInputElement>("input:checked")];
    kavach = new Kavach({ entities: chosen.map((b) => b.value) });
    update();
  });
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.dataset.type = type;
  label.append(box, swatch, LABELS[type]);
  entityBoxes.append(label);
}

/** The input with each detection wrapped in a labelled <mark>. Built from DOM
 * nodes, never HTML strings, so typed text cannot inject markup. */
function renderHighlights(text: string): number {
  const detections = kavach.scan(text);
  const nodes: Node[] = [];
  let last = 0;
  for (const d of detections) {
    nodes.push(document.createTextNode(text.slice(last, d.start)));
    const mark = document.createElement("mark");
    mark.dataset.type = d.entityType;
    mark.title = `${LABELS[d.entityType]} · confidence ${d.score.toFixed(2)}`;
    mark.textContent = text.slice(d.start, d.end);
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = LABELS[d.entityType];
    mark.append(tag);
    nodes.push(mark);
    last = d.end;
  }
  nodes.push(document.createTextNode(text.slice(last)));
  highlighted.replaceChildren(...nodes);
  return detections.length;
}

function renderCounts(found: number): void {
  if (!input.value.trim()) {
    counts.textContent = "Type or paste some text, or try a sample.";
    return;
  }
  if (found === 0) {
    counts.textContent = "No Indian personal data found.";
    return;
  }
  const parts = Object.entries(session.counts).map(
    ([type, n]) => `${n} ${LABELS[type as EntityType]}`,
  );
  counts.textContent = `Found ${found}: ${parts.join(", ")}.`;
}

/** A pretend AI reply that uses the placeholders, so the restore step has
 * something to work on. The visitor can edit it. */
function sampleReply(maskedText: string): string {
  const placeholders = [...new Set(maskedText.match(/\[[A-Z_]+_[0-9]+\]/g) ?? [])];
  if (placeholders.length === 0) return "";
  return `Thanks. I have noted ${placeholders.join(", ")} and will keep them as they are.`;
}

function update(): void {
  const text = input.value;
  session = kavach.session();
  const maskedText = session.mask(text);
  const found = renderHighlights(text);
  renderCounts(found);
  masked.textContent = maskedText;
  copy.disabled = maskedText.length === 0;
  if (!replyEdited) reply.value = sampleReply(maskedText);
  restored.textContent = session.unmask(reply.value);
}

let timer: number | undefined;
input.addEventListener("input", () => {
  window.clearTimeout(timer);
  timer = window.setTimeout(update, 120);
});

reply.addEventListener("input", () => {
  replyEdited = reply.value.length > 0;
  restored.textContent = session.unmask(reply.value);
});

for (const button of document.querySelectorAll<HTMLButtonElement>("[data-sample]")) {
  button.addEventListener("click", () => {
    input.value = SAMPLES[button.dataset.sample!] ?? "";
    replyEdited = false;
    update();
  });
}

copy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(masked.textContent ?? "");
    copy.textContent = "Copied";
  } catch {
    copy.textContent = "Copy failed";
  }
  window.setTimeout(() => (copy.textContent = "Copy"), 1500);
});

if (!input.value) input.value = SAMPLES.english!;
update();
