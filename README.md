# Kavach

**Keep Indian personal data out of LLM prompts.**

Kavach (कवच, "shield") detects Aadhaar, PAN, UPI IDs, bank details, phone numbers and more,
replaces them with placeholders before your prompt reaches an LLM, and restores them in the
reply. It runs locally, has no runtime dependencies, and uses deterministic rules (patterns,
checksums and context words) rather than another model.

```python
from kavach import Kavach

session = Kavach().session()

safe = session.mask("My PAN is ABCPE1234F, refund to rahul@okaxis")
# 'My PAN is [PAN_1], refund to [UPI_1]'

reply = call_llm(safe)  # the LLM only ever sees placeholders
print(session.unmask(reply))  # 'Refund for ABCPE1234F has been sent to rahul@okaxis'
```

> **Status:** early development (v0.1.0.dev0). Not yet on PyPI. Measured accuracy on a synthetic
> benchmark is in [Accuracy](#accuracy).

## Why

Security reviews often block LLM features in Indian fintech, insurance and health apps because
customer data would be sent to a third-party model. Generic PII tools cover some Indian IDs
([Microsoft Presidio](https://microsoft.github.io/presidio/) detects Aadhaar and PAN, for
example) but miss the identifiers these apps handle most: UPI IDs, IFSC codes, bank account
numbers, GSTINs and Indian phone formats, often written in Hinglish. Kavach fills those gaps and
makes masking reversible, so your app keeps working after the LLM responds.

## Install

From source, until the first PyPI release:

```bash
git clone https://github.com/harshita1615/kavach-pii.git
cd kavach-pii
pip install -e .
```

Requires Python 3.10+.

## What it detects

| Entity | Placeholder | How it is validated |
| --- | --- | --- |
| Aadhaar | `[AADHAAR_1]` | 12 digits, first digit 2-9, Verhoeff checksum. Spaces, dashes and line breaks allowed |
| PAN | `[PAN_1]` | 5 letters, 4 digits, 1 letter; 4th letter must be a valid holder type (P, C, H, F, A, T, B, L, J, G) |
| UPI ID | `[UPI_1]` | `name@handle`; known handles (okaxis, ybl, paytm, ...) score high, unknown handles need context |
| IFSC | `[IFSC_1]` | 4 letters, `0`, 6 letters or digits; known bank codes score higher |
| Bank account | `[BANK_ACCOUNT_1]` | 9-18 digits **and** a nearby context word ("account", "a/c", "khata", "खाता") |
| Mobile number | `[PHONE_1]` | 10 digits starting 6-9, optional `+91`, `0091`, `91` or `0`; contiguous, 5-5 or 3-3-4 |
| GSTIN | `[GSTIN_1]` | State code, embedded PAN, entity number, `Z`, base-36 check character |
| Email | `[EMAIL_1]` | Standard address format |

Context words in English, Hinglish and Devanagari ("mera aadhaar", "khata number", "मोबाइल")
raise confidence. When two matches overlap, Kavach keeps the higher-confidence, longer and more
specific one, so `9876543210@paytm` is one UPI ID, not a phone number.

Planned next: ABHA health ID, PIN code, voter ID, passport and vehicle numbers (v1.1); names and
addresses (v2).

## Usage

### Choose entities and mode

```python
k = Kavach(entities=["AADHAAR", "PAN", "UPI"], mode="mask")
```

| Mode | `session.mask()` returns | `session.unmask()` |
| --- | --- | --- |
| `mask` (default) | Text with placeholders | Restores the original values |
| `redact` | Text with placeholders | Cannot restore: no mapping is kept |
| `scan` | The text unchanged | Nothing to restore; use `session.counts` |

Switching mode is a config change, not a code change. `k.redact(text)` always redacts, whatever
the mode.

### Sessions

Use one session per conversation. Within a session the same value always gets the same
placeholder, across messages and formatting variants (`2345 6789 0123` and `234567890123` are
both `[AADHAAR_1]`). The mapping lives only in the session's memory: it is never logged, written
to disk or shown in `repr()`.

```python
session = k.session()
session.mask("PAN ABCPE1234F")  # 'PAN [PAN_1]'
session.mask("Is ABCPE1234F verified?")  # 'Is [PAN_1] verified?'
session.counts  # {'PAN': 2}, safe to log
session.clear()  # forget everything
```

Tell the model to keep placeholders intact:

```python
from kavach import SYSTEM_PROMPT  # "Keep every placeholder exactly as written ..."
```

`unmask()` tolerates small edits such as `[pan_1]` or `[ PAN_1 ]`, and leaves placeholders it
does not know unchanged rather than guessing.

### Streaming

LLM responses arrive in chunks, and a placeholder can be split across them (`[PA` + `N_1]`).
The stream unmasker holds back a possible partial placeholder until it is complete:

```python
stream = session.stream()
for chunk in llm_stream(safe):
    print(stream.feed(chunk), end="")
print(stream.flush())
```

### Scan only

```python
for d in Kavach().scan(text):
    print(d.entity_type, d.start, d.end, d.score)  # d.text_in(text) gives the value
```

### Command line

```bash
kavach scan chat.txt                  # types, line/column and confidence; never the values
kavach scan --json *.txt              # machine-readable
kavach scan --entities PAN,UPI -      # read from stdin
kavach redact chat.txt -o safe.txt    # replace PII with placeholders
```

`kavach scan` exits with 1 when it finds anything, so it works as a pre-commit or CI check.
There is no `mask` command: restoring later would require saving the mapping to disk, which
Kavach never does. Use the Python API for reversible masking.

## Accuracy

Measured on the **holdout split** of Kavach's [public synthetic benchmark](benchmark/): 600
sentences in English, Hinglish and Hindi, 581 labelled values, and 141 sentences with no PII but
plenty of look-alikes (order IDs, UTRs, PNRs, timestamps). The holdout templates were written after
Kavach was tuned and have never been used to tune it.

| Entity | Precision | Recall | Masked¹ |
| --- | ---: | ---: | ---: |
| Aadhaar | 94.9% | 100.0% | 100.0% |
| PAN | 100.0% | 100.0% | 100.0% |
| UPI ID | 100.0% | 93.6% | 93.6% |
| IFSC | 100.0% | 100.0% | 100.0% |
| Bank account | 100.0% | 83.7% | 84.5% |
| Mobile number | 74.6% | 100.0% | 100.0% |
| GSTIN | 100.0% | 100.0% | 100.0% |
| Email | 100.0% | 100.0% | 100.0% |

¹ The value was hidden by a detection of any type, so it would not reach the LLM.

Compared with Microsoft Presidio 2.2.364 on the same data:

| | Kavach | Presidio, default | Presidio + its Indian recognizers |
| --- | ---: | ---: | ---: |
| Values masked (all types) | **95.7%** | 55.9% | 79.3% |
| Clean sentences wrongly flagged | **32 / 141** | 44 / 141 | 65 / 141 |
| Latency, ms per 1,000 chars² | **0.8** | 93 | 92 |

² On one Windows laptop, Python 3.14. Presidio's time is mostly spaCy NER, which also finds names
and places that Kavach does not.

Where Kavach is weaker:

- **Phone false alarms.** A bare 10-digit number starting 6-9 (a coupon code or an order number
  with no label) looks exactly like a mobile number. Kavach errs towards masking.
- **Bank accounts without a keyword.** Kavach needs a context word nearby ("account", "a/c",
  "khata"), so a line like "Copying from my passbook: 50100…" is missed. Presidio masks more bank
  numbers here (91.5% vs 84.5%), mostly as other entity types.
- **UPI IDs with handles Kavach does not know**, when no "UPI" keyword is nearby.

Brackets-intact round trips (mask, then echo, reorder, change case or spacing, or stream in
chunks, then unmask) restored every value in all 467 holdout sentences Kavach masked. If the LLM
drops the brackets (`PAN_1`), nothing is restored.

Full tables, the tuning ("dev") split, and how to reproduce everything:
[benchmark/README.md](benchmark/README.md). Results are written by `python -m benchmark.run_eval`
and never edited by hand.

## Privacy principles

- Everything runs in-process. Kavach makes no network calls.
- Raw values are never logged, printed, stored or included in errors. A test fails the build if
  the package starts logging or printing.
- Audit output is limited to entity types and counts.
- All test and benchmark data is synthetic. Never file an issue with real personal data; use
  made-up values in the same format.

## Limitations

Kavach reduces the chance of PII reaching an LLM; it cannot guarantee that none will. It is a
risk-reduction tool, not legal advice, and using it does not by itself make an application
compliant with the DPDP Act or any other law.

Known gaps today:

- Names, addresses and free-text personal details are not detected (planned for v2).
- Landline numbers and special GSTIN formats (TDS/TCS, non-resident) are not covered.
- About 1 in 10 random 12-digit numbers starting 2-9 pass the Aadhaar checksum, so some
  unlabelled IDs may be masked as Aadhaar. A label right before the number ("Order", "UTR",
  "PNR", "Invoice") lowers the score.
- Numbers can get the wrong placeholder type (for example a phone number as
  `[BANK_ACCOUNT_1]`), though the value is still masked.
- If the LLM rewrites a placeholder beyond small case and spacing changes, it cannot be
  restored.

## Development

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use source .venv/bin/activate elsewhere
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

## Roadmap

1. **Python package** (this repo): core detection and masking ✅, benchmark ✅, PyPI release
2. **Chrome extension**: warn before PII is pasted into ChatGPT, Claude or Gemini; runs fully
   on-device
3. **Integrations**: web demo, OpenAI-compatible proxy, MCP server, Presidio recognizer pack,
   n8n node

## Related work

- [Microsoft Presidio](https://github.com/microsoft/presidio): general PII detection and
  anonymization. It ships recognizers for Aadhaar, PAN, GSTIN, Indian passport, voter ID and
  vehicle registration, though they are not enabled in its default English setup (as of
  2.2.364). Kavach aims to complement it, and a Presidio recognizer pack is planned.

## License

To be decided before the first release.
