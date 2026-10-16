/**
 * Content script: runs on the supported chatbot sites.
 *
 * Watches paste and send in the message box. If the text contains Indian PII,
 * it stops the paste or send and asks: Mask, Paste/Send anyway, or Cancel.
 * Everything happens in this page; nothing is sent anywhere. One masking
 * session per tab keeps placeholders consistent across messages in a chat.
 */

import { type EntityType, Kavach } from "../core/index.ts";
import { t } from "../shared/i18n.ts";
import { hasNote, withNote } from "../shared/note.ts";
import { addCaught, defaults, load, onChange } from "../shared/settings.ts";
import { looksLikeSendButton, type Site, siteForHost } from "../shared/sites.ts";
import { countByType, summarize } from "../shared/summary.ts";
import { showNotice, showWarning } from "./banner.ts";
import {
  appendAtEnd,
  composerFrom,
  findComposer,
  getText,
  insertAtCaret,
  replaceAll,
  saveSelection,
} from "./dom.ts";

const site = siteForHost(location.hostname);
if (site) start(site);

function start(site: Site): void {
  const kavach = new Kavach();
  const session = kavach.session();
  let settings = defaults();
  let bypassUntil = 0; // after "Send anyway", let the re-sent message through
  let lastComposer: HTMLElement | null = null;

  load().then((s) => (settings = s), () => {});
  onChange((s) => (settings = s));
  const enabled = () => settings.enabled[site.id];

  function record(counts: ReadonlyMap<EntityType, number>): void {
    addCaught(counts).catch(() => {});
  }

  function isSendButton(button: HTMLButtonElement): boolean {
    if (site.send.some((selector) => button.matches(selector))) return true;
    const label = [button.getAttribute("aria-label"), button.getAttribute("data-testid"), button.title]
      .filter(Boolean)
      .join(" ");
    return looksLikeSendButton(label);
  }

  function findSendButton(): HTMLButtonElement | null {
    for (const selector of site.send) {
      const b = document.querySelector<HTMLButtonElement>(selector);
      if (b) return b;
    }
    return [...document.querySelectorAll("button")].find(isSendButton) ?? null;
  }

  // --- paste -----------------------------------------------------------------------

  document.addEventListener(
    "paste",
    (event) => {
      if (!enabled()) return;
      const composer = composerFrom(event.target);
      const text = event.clipboardData?.getData("text/plain") ?? "";
      if (!composer || !text) return;
      const detections = kavach.scan(text);
      if (detections.length === 0) return;

      event.preventDefault();
      event.stopImmediatePropagation();
      const restore = saveSelection(composer);
      const counts = countByType(detections);
      record(counts);

      showWarning(t("banner_paste_title", [summarize(counts, t)]), t("banner_body"), [
        {
          label: t("btn_mask"),
          primary: true,
          run: () => {
            restore();
            insertAtCaret(composer, session.mask(text));
            const note = t("masked_note");
            if (!hasNote(getText(composer), note)) appendAtEnd(composer, `\n\n${note}`);
          },
        },
        {
          label: t("btn_paste_anyway"),
          run: () => {
            restore();
            insertAtCaret(composer, text);
          },
        },
        { label: t("btn_cancel"), run: restore },
      ]);
    },
    true,
  );

  // --- send --------------------------------------------------------------------------

  /** If the message contains PII, stop the send and ask the user what to do. */
  function checkSend(event: Event, composer: HTMLElement | null, resend: () => void): void {
    if (!enabled() || !composer || Date.now() < bypassUntil) return;
    const text = getText(composer);
    const detections = kavach.scan(text);
    if (detections.length === 0) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    const counts = countByType(detections);
    record(counts);

    showWarning(t("banner_send_title", [summarize(counts, t)]), t("banner_body"), [
      {
        label: t("btn_mask"),
        primary: true,
        run: () => {
          // Replace and let the user review; never send on their behalf after masking.
          replaceAll(composer, withNote(session.mask(getText(composer)), t("masked_note")));
          showNotice(t("notice_masked"));
        },
      },
      {
        label: t("btn_send_anyway"),
        run: () => {
          bypassUntil = Date.now() + 1500;
          resend();
        },
      },
      { label: t("btn_cancel"), run: () => composer.focus() },
    ]);
  }

  document.addEventListener(
    "keydown",
    (event) => {
      if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
      const composer = composerFrom(event.target);
      if (!composer) return;
      lastComposer = composer;
      checkSend(event, composer, () => {
        const button = findSendButton();
        if (button) {
          button.click();
        } else {
          composer.dispatchEvent(
            new KeyboardEvent("keydown", { key: "Enter", code: "Enter", bubbles: true, cancelable: true }),
          );
        }
      });
    },
    true,
  );

  document.addEventListener(
    "click",
    (event) => {
      const button = (event.target as Element | null)?.closest?.("button");
      if (!button || !isSendButton(button)) return;
      checkSend(event, findComposer(site) ?? lastComposer, () => button.click());
    },
    true,
  );

  document.addEventListener(
    "focusin",
    (event) => {
      const composer = composerFrom(event.target);
      if (composer) lastComposer = composer;
    },
    true,
  );
}
