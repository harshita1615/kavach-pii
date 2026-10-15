/**
 * The warning banner, in a closed shadow root so the page's CSS can't change
 * it and the page's scripts can't read it. It only ever shows counts and
 * fixed strings; detected values are never put in the DOM.
 */

export interface Action {
  label: string;
  primary?: boolean;
  run: () => void;
}

const STYLE = `
  :host { all: initial; }
  .wrap {
    --bg: #ffffff; --fg: #1f2328; --muted: #59636e; --border: #d1d9e0;
    --accent: #1d4ed8; --accent-fg: #ffffff; --shadow: 0 8px 28px rgb(0 0 0 / 0.18);
    position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%);
    z-index: 2147483647; box-sizing: border-box;
    width: min(560px, calc(100vw - 32px)); padding: 16px;
    background: var(--bg); color: var(--fg); border: 1px solid var(--border);
    border-radius: 12px; box-shadow: var(--shadow);
    font: 14px/1.45 system-ui, -apple-system, "Segoe UI", "Noto Sans Devanagari", sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    .wrap { --bg: #1c2128; --fg: #e6edf3; --muted: #9198a1; --border: #3d444d;
            --accent: #4493f8; --accent-fg: #0d1117; }
  }
  .head { display: flex; gap: 10px; align-items: flex-start; }
  .shield { flex: none; width: 22px; height: 22px; color: var(--accent); }
  .title { margin: 0; font-weight: 600; font-size: 15px; }
  .body { margin: 4px 0 0; color: var(--muted); }
  .actions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; margin-top: 14px; }
  button {
    font: inherit; padding: 6px 14px; border-radius: 8px; cursor: pointer;
    border: 1px solid var(--border); background: transparent; color: var(--fg);
  }
  button.primary { background: var(--accent); border-color: var(--accent); color: var(--accent-fg); font-weight: 600; }
  button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .notice { padding: 10px 16px; }
`;

const SHIELD_SVG = `<svg class="shield" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Zm-1.2 13.6-3.4-3.4 1.4-1.4 2 2 4.6-4.6 1.4 1.4-6 6Z"/></svg>`;

let current: { host: HTMLElement; previousFocus: Element | null } | null = null;

function mount(build: (root: ShadowRoot) => HTMLElement): HTMLElement {
  close();
  const host = document.createElement("kavach-banner");
  const root = host.attachShadow({ mode: "closed" });
  const style = document.createElement("style");
  style.textContent = STYLE;
  root.append(style, build(root));
  document.documentElement.append(host);
  current = { host, previousFocus: document.activeElement };
  return host;
}

export function close(): void {
  current?.host.remove();
  current = null;
}

/** Show a warning with buttons. Esc runs the last action (Cancel). */
export function showWarning(title: string, body: string, actions: Action[]): void {
  mount(() => {
    const wrap = document.createElement("div");
    wrap.className = "wrap";
    wrap.setAttribute("role", "alertdialog");
    wrap.setAttribute("aria-modal", "false");
    wrap.setAttribute("aria-labelledby", "kavach-title");
    wrap.setAttribute("aria-describedby", "kavach-body");

    const head = document.createElement("div");
    head.className = "head";
    head.innerHTML = SHIELD_SVG; // static markup only
    const text = document.createElement("div");
    const h = document.createElement("p");
    h.className = "title";
    h.id = "kavach-title";
    h.textContent = title;
    const p = document.createElement("p");
    p.className = "body";
    p.id = "kavach-body";
    p.textContent = body;
    text.append(h, p);
    head.append(text);

    const row = document.createElement("div");
    row.className = "actions";
    const buttons = actions.map((action) => {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = action.label;
      if (action.primary) b.className = "primary";
      b.addEventListener("click", () => {
        close();
        action.run();
      });
      return b;
    });
    // Cancel on the left, primary on the right; the primary button gets focus.
    row.append(...buttons.slice().reverse());

    wrap.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
        actions.at(-1)?.run();
      }
      e.stopPropagation(); // keep the page's shortcuts from firing behind the banner
    });

    queueMicrotask(() => buttons.find((_, i) => actions[i]!.primary)?.focus());
    wrap.append(head, row);
    return wrap;
  });
}

/** A short confirmation that disappears by itself. */
export function showNotice(message: string, ms = 4000): void {
  const host = mount(() => {
    const wrap = document.createElement("div");
    wrap.className = "wrap notice";
    wrap.setAttribute("role", "status");
    wrap.textContent = message;
    return wrap;
  });
  setTimeout(() => {
    if (current?.host === host) close();
  }, ms);
}
