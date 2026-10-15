/**
 * Supported chatbot sites and how to find their message box and send button.
 *
 * Chatbot UIs change often. Everything site-specific lives here, so a layout
 * change means editing one list. Each site also falls back to generic rules
 * (any focused textarea or contenteditable; any button labelled "send"), so a
 * renamed selector degrades gracefully instead of silently disabling Kavach.
 */

export interface Site {
  readonly id: "chatgpt" | "claude" | "gemini";
  readonly name: string;
  readonly hosts: readonly string[];
  /** Message box, most specific first. */
  readonly composer: readonly string[];
  /** Send button, most specific first. */
  readonly send: readonly string[];
}

export const SITES: readonly Site[] = [
  {
    id: "chatgpt",
    name: "ChatGPT",
    hosts: ["chatgpt.com"],
    composer: ["#prompt-textarea", "form [contenteditable='true']", "form textarea"],
    send: ["button[data-testid='send-button']", "#composer-submit-button"],
  },
  {
    id: "claude",
    name: "Claude",
    hosts: ["claude.ai"],
    composer: ["div.ProseMirror[contenteditable='true']", "fieldset [contenteditable='true']"],
    send: ["button[aria-label='Send message']", "button[aria-label='Send Message']"],
  },
  {
    id: "gemini",
    name: "Gemini",
    hosts: ["gemini.google.com"],
    composer: ["rich-textarea .ql-editor[contenteditable='true']", "rich-textarea [contenteditable='true']"],
    send: ["button.send-button", "button[aria-label='Send message']"],
  },
];

export function siteForHost(hostname: string): Site | undefined {
  const host = hostname.toLowerCase();
  return SITES.find((site) => site.hosts.some((h) => host === h || host.endsWith(`.${h}`)));
}

/** Generic send-button test, used when no site selector matches. */
export function looksLikeSendButton(label: string): boolean {
  return /\bsend\b|भेजें/i.test(label);
}
