# Kavach Indian PII benchmark

A fully synthetic benchmark for detecting Indian personal data in short, chat-like text.
No real person's data is used anywhere.

## Splits

| Split | File | Sentences | Labelled entities | Sentences with no PII | Seed |
| --- | --- | ---: | ---: | ---: | ---: |
| dev | `dataset/kavach_bench_v1.jsonl` | 1,500 | 1,925 | 374 | 2026 |
| holdout | `dataset/kavach_bench_v1_holdout.jsonl` | 600 | 581 | 141 | 7 |

**Quote the holdout numbers.** Kavach's rules were tuned while looking at the dev split. In
particular, the rule that lowers confidence for a number labelled directly before as "Order no.",
"UTR" and so on was added after studying dev false alarms. The holdout templates were written after
that tuning, with different phrasing (chat abbreviations, numbers with no label in front, values at
the start of a sentence), and Kavach has not been changed in response to them.

Both splits were written by Kavach's author, so even the holdout split shares the author's idea of
what Indian PII looks like in text. An independent dataset would be a stronger test; contributions
are welcome.

## Format

One JSON object per line:

```json
{"id": "kb1-00003", "lang": "en", "scenario": "loan",
 "text": "Applicant mobile 9815188447, email yauvanichauhan5@example.com, PAN LLOFN1698P.",
 "entities": [{"type": "PHONE", "start": 17, "end": 27},
              {"type": "EMAIL", "start": 35, "end": 62},
              {"type": "PAN", "start": 68, "end": 78}]}
```

- `type`: AADHAAR, PAN, UPI, IFSC, BANK_ACCOUNT, PHONE, GSTIN or EMAIL
- `start` / `end`: character offsets, end exclusive
- `lang`: `en`, `hinglish` (romanised Hindi) or `hi` (Devanagari)
- `scenario`: support_chat, kyc, loan, bank_complaint, customer_service or system

Names, cities and dates appear in the text but are not labelled. They are out of scope for v1.

## How it is built

`generators/templates.py` holds sentence templates with slots. `generators/ids.py` fills the slots:

- **Valid fake identifiers.** Aadhaar numbers carry a correct Verhoeff check digit, GSTINs a
  correct check character, and PANs a valid holder-type letter. IDs come in several formats
  (spaced, dashed, `+91`, lowercase PAN and so on).
- **IDs Kavach was not told about.** About 10% of UPI IDs use handles that are not in Kavach's
  known-handle list, and about 10% of IFSCs use unlisted bank codes.
- **Hard negatives.** These are unlabelled values that look like PII: 12-digit order IDs and UTR
  numbers, timestamps, 10-digit order numbers and PNRs shaped like phone numbers, PANs with an
  invalid holder letter, Aadhaar-shaped numbers with a wrong check digit, PIN codes, OTPs,
  amounts and tracking numbers.
- **Synthetic people.** Names and cities come from Faker (`en_IN`), and email domains are
  reserved (`example.com`) or fake.

Random IDs and phone numbers can coincide with real ones by chance. That is unavoidable for these
formats, but no value is derived from real data.

```bash
pip install -e ".[benchmark]"
python -m benchmark.generators.build    # regenerates both splits (deterministic per seed and Faker version)
```

## Metrics

- **Strict precision, recall and F1 per entity.** A prediction counts only with the exact type and
  the exact span.
- **Masked recall.** The share of labelled values fully covered by predictions of *any* type. A
  phone number masked as `[BANK_ACCOUNT_1]` still never reaches the LLM, so this is the
  privacy-relevant number.
- **False alarms.** Predictions of a benchmark entity type that overlap no labelled value. For
  Presidio, types with no benchmark equivalent (PERSON, LOCATION and so on) are not counted as false
  alarms, because those can be real PII that this benchmark simply does not label.
- **Latency.** The median of repeated runs over the whole split, in milliseconds per 1,000
  characters. It depends on the machine.
- **Round trip.** Mask, rewrite the masked text the way an LLM might, unmask, and check that every
  value comes back. The rewrite styles are: echoed, placeholders reordered, lowercase with spaces
  inside brackets, streamed in random 1–8 character chunks, and brackets dropped. The last style is
  a known failure, included so the table shows it.

## Comparison with Presidio

`--presidio` runs Microsoft Presidio (`presidio-analyzer`, spaCy `en_core_web_lg`) in two setups:

- **presidio-default**: `AnalyzerEngine()` exactly as it comes. In version 2.2.364 its default
  English recognizers include no Indian identifiers.
- **presidio+india**: the same, plus Presidio's own `InAadhaarRecognizer`, `InPanRecognizer`,
  `InGstinRecognizer`, `InPassportRecognizer`, `InVoterRecognizer` and
  `InVehicleRegistrationRecognizer`.

Presidio is run with its default score threshold. Presidio is a general-purpose framework, and this
benchmark is built around the identifiers Kavach targets, so the comparison shows where Kavach adds
coverage for Indian data. It is not a ranking of the two tools overall.

```bash
pip install -e ".[benchmark]"
python -m spacy download en_core_web_lg
python -m benchmark.run_eval --presidio
```

## Results

- [`results/holdout/results.md`](results/holdout/results.md): the numbers to quote
- [`results/dev/results.md`](results/dev/results.md): the tuning split, optimistic
- [`results/dev_before_tuning/results.md`](results/dev_before_tuning/results.md): dev before the
  negative-label rule and the bank/phone tie-break change, kept for transparency
