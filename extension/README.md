# Kavach browser extension

Warns before Indian personal data is pasted or sent into ChatGPT, Claude or Gemini, and offers to
mask it. Manifest V3; runs entirely on the device, with no network requests.

## Layout

| Path | What |
| --- | --- |
| `src/core/` | Detection engine, a TypeScript port of the Python package. Pinned to it by the parity test |
| `src/core/rules.json` | Keywords, handles, bank codes and scores, generated from Python. Do not edit |
| `src/content/` | Content script: paste/send interception, warning banner, message-box editing |
| `src/shared/sites.ts` | Per-site selectors. Edit here when a chatbot changes its layout |
| `src/popup/` | Toolbar popup: per-site switches and counts |
| `src/demo/` | The website demo (kavach.bigforge.tech/demo/). `npm run build:demo` bundles it into `docs/demo/demo.js`, which is committed; CI fails if it is stale |
| `_locales/` | English and Hindi strings |
| `store/LISTING.md` | Chrome Web Store form answers |

## Develop

```bash
npm install
npm test            # unit, parity (vs Python) and privacy tests
npm run typecheck
npm run build       # -> dist/
npm run package     # -> kavach-extension-<version>.zip
```

Load `dist/` with **chrome://extensions → Developer mode → Load unpacked**. After rebuilding,
click reload on the Kavach card **and reload the chatbot tabs**: Chrome does not replace an
extension's script in tabs that were already open.

## Keeping Python and TypeScript in step

Detection rules live in the Python package. After changing them:

```bash
python scripts/export_rules.py    # -> src/core/rules.json
python scripts/export_parity.py   # -> test/fixtures/parity.json
cd extension && npm test
```

CI regenerates both files and fails if the committed copies are stale or if TypeScript disagrees
with Python on any of the 2,140 parity cases.
