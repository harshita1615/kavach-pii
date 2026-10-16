# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-10-16

### Added

- MCP server, `kavach-mcp`, installed with `pip install "kavach-pii[mcp]"`. Tools: `scan_file`
  and `redact_file`, which let an AI assistant work from a redacted copy of a file without
  seeing the values, and `scan_text` and `redact_text`. File access is limited to the `--root`
  folders, input files are never overwritten, and results never contain detected values.
- Project website: https://kavach-pii.vercel.app/

### Fixed

- `scan()` and `mask()` raised `ValueError` on Aadhaar-shaped text mixing ASCII and Devanagari
  digits (for example `2३४५ ६७८९ ०१२३`). All detectors now match ASCII digits only, so
  Devanagari digits are ignored consistently instead of being picked up by some detectors and
  crashing others.

## [0.1.0] - 2026-10-11

First public release.

### Added

- Detectors for Aadhaar (Verhoeff checksum), PAN (holder type), UPI ID, IFSC, bank account
  number (context required), Indian mobile number, GSTIN (check character) and email.
- Context words in English, Hinglish and Devanagari that raise confidence, and labels such as
  "Order no." or "UTR" that lower it for plain numbers.
- Overlap resolution: higher confidence, then longer span, then more specific type.
- `Kavach` API with `scan()`, `redact()` and `session()`; `mask`, `redact` and `scan` modes.
- Reversible masking with typed placeholders (`[PAN_1]`), held in memory only; tolerant
  `unmask()`; stream unmasker for chunked LLM output; `SYSTEM_PROMPT`.
- `kavach scan` and `kavach redact` command-line tools.
- Synthetic benchmark (dev and holdout splits), evaluation script and Presidio comparison.
