# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - not yet released

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
