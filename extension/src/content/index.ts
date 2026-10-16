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
import { close, showNotice, showWarning } from "./banner.ts";
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

  // When the extension is updated or reloaded, Chrome leaves this copy running
  // in already-open tabs but cuts its connection ("Extension context
  // invalidated"). An orphaned copy must switch itself off rather than throw
  // errors or keep intercepting sends; the page's next load gets the new copy.
  const lifetime = new AbortController();
  const alive = (): boolean => {
    try {
      return Boolean(chrome.runtime?.id);
    } catch {
      return false;
    }
  };

  function listen<K extends keyof DocumentEventMap>(
    type: K,
    handler: (event: DocumentEventMap[K]) => void,
    _capture: true,
  ): void {
    document.addEventListener(
      type,
      (event) => {
        if (!alive()) {
          lifetime.abort();
          close();
          return;
        }
        try {
          handler(event);
        } catch (error) {
          if (alive()) throw error;
          lifetime.abort();
          close();
        }
      },
      { capture: true, signal: lifetime.signal },
    );
  }

  load().then((s) => (settings = s), () => {});
  try {
    onChange((s) => (settings = s));
  } catch {
    return; // already orphaned before it started
  }
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

  listen(
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
            if (!hasNote(getText(composer), note)) appendAtEnd(composer, `\n${note}`);
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

  listen(
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

  listen(
    "click",
    (event) => {
      const button = (event.target as Element | null)?.closest?.("button");
      if (!button || !isSendButton(button)) return;
      checkSend(event, findComposer(site) ?? lastComposer, () => button.click());
    },
    true,
  );

  listen(
    "focusin",
    (event) => {
      const composer = composerFrom(event.target);
      if (composer) lastComposer = composer;
    },
    true,
  );
}
