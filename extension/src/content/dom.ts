/** Reading and writing chatbot message boxes (textarea or contenteditable). */

import type { Site } from "../shared/sites.ts";

const EDITABLE = "[contenteditable='true'], [contenteditable=''], [contenteditable='plaintext-only']";

/** The message box an event happened in, if any. */
export function composerFrom(target: EventTarget | null): HTMLElement | null {
  if (!(target instanceof Element)) return null;
  if (target instanceof HTMLTextAreaElement) return target;
  return target.closest<HTMLElement>(EDITABLE);
}

/** The site's message box, using its selectors. */
export function findComposer(site: Site): HTMLElement | null {
  for (const selector of site.composer) {
    const el = document.querySelector<HTMLElement>(selector);
    if (el) return el;
  }
  return null;
}

export function getText(el: HTMLElement): string {
  return el instanceof HTMLTextAreaElement ? el.value : el.innerText;
}

/** Capture the caret/selection now, to put it back after the banner took focus. */
export function saveSelection(el: HTMLElement): () => void {
  if (el instanceof HTMLTextAreaElement) {
    const { selectionStart, selectionEnd } = el;
    return () => {
      el.focus();
      el.setSelectionRange(selectionStart, selectionEnd);
    };
  }
  const selection = window.getSelection();
  const range =
    selection && selection.rangeCount && el.contains(selection.anchorNode)
      ? selection.getRangeAt(0).cloneRange()
      : null;
  return () => {
    el.focus();
    const current = window.getSelection();
    if (range && current) {
      current.removeAllRanges();
      current.addRange(range);
    }
  };
}

/**
 * Insert text at the caret the way typing would, so the page's editor
 * (React, ProseMirror, Quill) notices. execCommand is deprecated but is still
 * the one input path every rich editor listens to.
 */
export function insertAtCaret(el: HTMLElement, text: string): void {
  if (document.execCommand("insertText", false, text)) return;
  if (el instanceof HTMLTextAreaElement) {
    el.setRangeText(text, el.selectionStart, el.selectionEnd, "end");
  } else {
    const selection = window.getSelection();
    if (selection?.rangeCount) {
      const range = selection.getRangeAt(0);
      range.deleteContents();
      range.insertNode(document.createTextNode(text));
      range.collapse(false);
    } else {
      el.append(text);
    }
  }
  el.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
}

/** Move the caret to the end of the message and insert text there. */
export function appendAtEnd(el: HTMLElement, text: string): void {
  el.focus();
  if (el instanceof HTMLTextAreaElement) {
    el.setSelectionRange(el.value.length, el.value.length);
  } else {
    const selection = window.getSelection();
    selection?.selectAllChildren(el);
    selection?.collapseToEnd();
  }
  insertAtCaret(el, text);
}

/** Replace the whole message with text. */
export function replaceAll(el: HTMLElement, text: string): void {
  el.focus();
  if (el instanceof HTMLTextAreaElement) {
    el.select();
  } else {
    window.getSelection()?.selectAllChildren(el);
  }
  insertAtCaret(el, text);
}
