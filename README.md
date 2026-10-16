# Kavach

**Keep Indian personal data out of LLM prompts.**

Kavach (कवच, "shield") detects Aadhaar, PAN, UPI IDs, bank details, phone numbers and more,
replaces them with placeholders before your prompt reaches an LLM, and restores them in the
reply. It runs locally, has no runtime dependencies, and uses deterministic rules (patterns,
checksums and context words) rather than another model.

**Website:** [kavach.bigforge.tech](https://kavach.bigforge.tech/) · **[Try it in your browser](https://kavach.bigforge.tech/demo/)**

```python
from kavach import Kavach

session = Kavach().session()

safe = session.mask("My PAN is ABCPE1234F, refund to rahul@okaxis")
# 'My PAN is [PAN_1], refund to [UPI_1]'

reply = call_llm(safe)  # the LLM only ever sees placeholders
print(session.unmask(reply))  # 'Refund for ABCPE1234F has been sent to rahul@okaxis'
```

> **Status:** alpha (v0.2.0). The API may change before 1.0. Measured accuracy on a synthetic
> benchmark is in [Accuracy](#accuracy).

## Why

Security reviews often block LLM features in Indian fintech, insurance and health apps because
customer data would be sent to a third-party model. Generic PII tools cover some Indian IDs
([Microsoft Presidio](https://microsoft.github.io/presidio/) detects Aadhaar and PAN, for
example) but miss the identifiers these apps handle most: UPI IDs, IFSC codes, bank account
numbers, GSTINs and Indian phone formats, often written in Hinglish. Kavach fills those gaps and
makes masking reversible, so your app keeps working after the LLM responds.

## Install

```bash
pip install kavach-pii
```

The package is `kavach-pii`; the import is `kavach`. Requires Python 3.10+ and has no
dependencies. For the [MCP server](#mcp-server), install `kavach-pii[mcp]`. (An unrelated PyPI package named `kavach` also uses the `kavach` import name; do
not install both in the same environment.)

To try unreleased changes, install from source:

```bash
pip install git+https://github.com/harshita1615/kavach-pii.git
```

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

### MCP server

`kavach-mcp` lets an AI assistant (Claude Desktop, Claude Code, Cursor and other
[MCP](https://modelcontextprotocol.io/) clients) check and redact files without reading the
personal data in them.

```bash
pip install "kavach-pii[mcp]"
```

The extra installs the official MCP Python SDK; plain `pip install kavach-pii` stays
dependency-free. The server runs locally over stdio and makes no network calls.

| Tool | What the assistant gets back |
| --- | --- |
| `scan_file(path)` | Types, line and column numbers and counts. Never the values |
| `redact_file(path, output_path?, overwrite?)` | Writes `<name>.redacted.<ext>` with placeholders; returns its path and counts |
| `scan_text(text)` | Types, positions and counts |
| `redact_text(text)` | The text with placeholders, for sending on to a message, email, ticket or log |

Ask it to "summarise customers.csv using Kavach" and it scans the file, writes
`customers.redacted.csv` and reads only that copy, so the real values never enter the
conversation. The server's instructions tell the assistant to work this way.

**Connect it.** `--root` sets the folders the file tools may use (default: the current folder);
repeat it for more than one.

- Claude Code: `claude mcp add kavach -- kavach-mcp --root /path/to/data`, or a `.mcp.json` in the
  project:

  ```json
  {
    "mcpServers": {
      "kavach": { "command": "kavach-mcp", "args": ["--root", "/path/to/data"] }
    }
  }
  ```

- Claude Desktop: add the same `"kavach"` entry under `mcpServers` in
  `claude_desktop_config.json`. On Windows, give the full path to `kavach-mcp.exe` (or to
  `python.exe` with `"args": ["-m", "kavach.mcp_server", "--root", ...]`).
- Without installing: `uvx --from "kavach-pii[mcp]" kavach-mcp --root /path/to/data`.

`--entities` and `--threshold` work as in the command-line tool.

**Safety.** The file tools refuse paths outside `--root`, including through `..` or symlinks.
They never overwrite the input file, and replace an existing redacted copy only with
`overwrite=true`. Files must be UTF-8 text, up to 10 MB. Redaction keeps no mapping, so nothing
can be restored through the server.

**Limits.** Any text the assistant passes to `scan_text` or `redact_text`, it has already read;
those tools protect where the text goes next, not the conversation itself. Kavach also cannot
stop an assistant from opening the original file with its own file tools. To rule that out in
Claude Code, keep the originals in a folder it may not read and write the redacted copies
elsewhere, for example in `.claude/settings.json`:

```json
{ "permissions": { "deny": ["Read(./data/**)"] } }
```

with `redact_file(path="data/customers.csv", output_path="safe/customers.csv")`.

## Accuracy

Measured on the **holdout split** of Kavach's
[public synthetic benchmark](https://github.com/harshita1615/kavach-pii/tree/main/benchmark): 600
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
[benchmark/README.md](https://github.com/harshita1615/kavach-pii/blob/main/benchmark/README.md).
Results are written by `python -m benchmark.run_eval`
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
- IDs written with Devanagari digits (२३४५…) are not detected; only ASCII digits are.
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

1. **Python package** (this repo): core detection and masking ✅, benchmark ✅, PyPI release ✅
2. **Chrome extension** ([extension/](https://github.com/harshita1615/kavach-pii/tree/main/extension)):
   warns before PII is pasted or sent into ChatGPT, Claude or Gemini; runs fully on-device.
   Built and tested; in Chrome Web Store review
3. **Integrations**: [MCP server](#mcp-server) ✅, [website](https://kavach.bigforge.tech/) ✅,
   [web demo](https://kavach.bigforge.tech/demo/) ✅; next: OpenAI-compatible proxy, Presidio
   recognizer pack, n8n node

## Related work

- [Microsoft Presidio](https://github.com/microsoft/presidio): general PII detection and
  anonymization. It ships recognizers for Aadhaar, PAN, GSTIN, Indian passport, voter ID and
  vehicle registration, though they are not enabled in its default English setup (as of
  2.2.364). Kavach aims to complement it, and a Presidio recognizer pack is planned.

## License

[MIT](https://github.com/harshita1615/kavach-pii/blob/main/LICENSE) © 2026 Harshita Chaudhary
