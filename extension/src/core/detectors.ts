/**
 * Entity detectors, ported from kavach/detectors/*.py.
 *
 * Each pattern is a line-by-line port of its Python counterpart; see the
 * Python files for format sources and design notes. Behaviour is pinned by
 * the parity test against the Python package's output.
 */

import { hasContext } from "./context.ts";
import { RULES } from "./rules.ts";
import { W, W_CHARS } from "./regex.ts";
import { type Detection, type Detector, type EntityType, makeDetection } from "./types.ts";
import { gstinIsValid, verhoeffIsValid } from "./validators.ts";

const NON_DIGITS = /[^0-9]/g;
const HOLDER = RULES.panHolderTypes;
const KNOWN_HANDLES = new Set(RULES.upiKnownHandles);
const KNOWN_BANK_CODES = new Set(RULES.ifscKnownBankCodes);
const STATE_CODES = new Set(RULES.gstinStateCodes);
const S = RULES.scores;

function simple(
  entityType: EntityType,
  name: string,
  pattern: RegExp,
  score: (match: RegExpMatchArray) => number | null,
  normalize: (value: string) => string,
  requiresContext = false,
): Detector {
  return {
    entityType,
    name,
    requiresContext,
    normalize,
    detect(text: string): Detection[] {
      const detections: Detection[] = [];
      for (const match of text.matchAll(pattern)) {
        const value = score(match);
        if (value !== null) {
          const start = match.index!;
          detections.push(makeDetection(entityType, start, start + match[0].length, value, name));
        }
      }
      return detections;
    },
  };
}

// --- Aadhaar ---------------------------------------------------------------------

const AADHAAR_SEP = String.raw`(?:[ \t]*-[ \t]*|[ \t]+|\r?\n)?`;
const AADHAAR_PATTERN = new RegExp(
  `(?<!${W})(?<!(?<!${W})[0-9]{4}[ -])` +
    `[2-9][0-9]{3}${AADHAAR_SEP}[0-9]{4}${AADHAAR_SEP}[0-9]{4}` +
    `(?![ -]?[0-9]{4}(?!${W}))(?!${W})`,
  "gu",
);
const digitsOnly = (value: string) => value.replace(NON_DIGITS, "");

export const aadhaar = simple(
  "AADHAAR",
  "aadhaar",
  AADHAAR_PATTERN,
  (m) => {
    const digits = digitsOnly(m[0]);
    return digits.length === 12 && verhoeffIsValid(digits) ? S.AADHAAR : null;
  },
  digitsOnly,
);

// --- PAN ---------------------------------------------------------------------------

const PAN_PATTERN = new RegExp(
  `(?<![A-Za-z0-9])[A-Z]{3}[${HOLDER}][A-Z][ -]?[0-9]{4}[ -]?[A-Z](?![A-Za-z0-9])`,
  "giu",
);

export const pan = simple(
  "PAN",
  "pan",
  PAN_PATTERN,
  () => S.PAN,
  (value) => value.replace(/[ -]/g, "").toUpperCase(),
);

// --- UPI ---------------------------------------------------------------------------

const UPI_PATTERN = new RegExp(
  `(?<![${W_CHARS}.\\-@])` +
    `[a-z0-9][a-z0-9._\\-]{1,255}@(?<handle>[a-z][a-z0-9]{1,63})` +
    `(?![${W_CHARS}@]|[.\\-][a-z0-9])`,
  "giu",
);

export const upi = simple(
  "UPI",
  "upi",
  UPI_PATTERN,
  (m) =>
    KNOWN_HANDLES.has(m.groups!.handle!.toLowerCase())
      ? S.UPI_KNOWN_HANDLE
      : S.UPI_UNKNOWN_HANDLE,
  (value) => value.toLowerCase(),
);

// --- IFSC --------------------------------------------------------------------------

const IFSC_PATTERN = /(?<![A-Za-z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Za-z0-9])/giu;

export const ifsc = simple(
  "IFSC",
  "ifsc",
  IFSC_PATTERN,
  (m) =>
    KNOWN_BANK_CODES.has(m[0].slice(0, 4).toUpperCase())
      ? S.IFSC_KNOWN_BANK
      : S.IFSC_UNKNOWN_BANK,
  (value) => value.toUpperCase(),
);

// --- Bank account ------------------------------------------------------------------

const BANK_PATTERN = new RegExp(
  `(?<![${W_CHARS}+\\-])` +
    `(?:[0-9]{9,18}|[0-9]{3,6}(?:[ \\-][0-9]{3,6}){1,5})` +
    `(?!${W}|[ \\-]?[0-9])`,
  "gu",
);

export const bankAccount: Detector = {
  entityType: "BANK_ACCOUNT",
  name: "bank_account",
  requiresContext: true,
  normalize: digitsOnly,
  detect(text: string): Detection[] {
    const detections: Detection[] = [];
    for (const m of text.matchAll(BANK_PATTERN)) {
      const start = m.index!;
      const end = start + m[0].length;
      const length = digitsOnly(m[0]).length;
      if (length >= 9 && length <= 18 && hasContext(text, start, end, "BANK_ACCOUNT")) {
        detections.push(makeDetection("BANK_ACCOUNT", start, end, S.BANK_ACCOUNT, "bank_account"));
      }
    }
    return detections;
  },
};

// --- Phone -------------------------------------------------------------------------

const PHONE_PATTERN = new RegExp(
  `(?<![${W_CHARS}+])` +
    String.raw`(?<prefix>(?:\+|00)91[ \-]?|\(\+?91\)[ \-]?|91[ \-]?|0)?` +
    String.raw`(?:[6-9][0-9]{9}|[6-9][0-9]{4}[ \-][0-9]{5}|[6-9][0-9]{2}[ \-][0-9]{3}[ \-][0-9]{4})` +
    `(?!${W}|[ \\-]?[0-9])`,
  "gu",
);

export const phone = simple(
  "PHONE",
  "phone",
  PHONE_PATTERN,
  (m) => {
    const prefix = m.groups?.prefix ?? "";
    const international = ["+", "00", "(+"].some((p) => prefix.startsWith(p));
    return international ? S.PHONE_INTERNATIONAL : S.PHONE;
  },
  (value) => digitsOnly(value).slice(-10),
);

// --- GSTIN -------------------------------------------------------------------------

const GSTIN_PATTERN = new RegExp(
  `(?<![A-Za-z0-9])(?<state>[0-9]{2})[A-Z]{3}[${HOLDER}][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z](?![A-Za-z0-9])`,
  "giu",
);

export const gstin = simple(
  "GSTIN",
  "gstin",
  GSTIN_PATTERN,
  (m) => (STATE_CODES.has(m.groups!.state!) && gstinIsValid(m[0]) ? S.GSTIN : null),
  (value) => value.toUpperCase(),
);

// --- Email -------------------------------------------------------------------------

const LABEL = String.raw`[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?`;
const EMAIL_PATTERN = new RegExp(
  `(?<![${W_CHARS}.%+\\-])` +
    String.raw`[A-Za-z0-9][A-Za-z0-9._%+\-]{0,63}` +
    `@${LABEL}(?:\\.${LABEL})*\\.[A-Za-z]{2,24}` +
    `(?![${W_CHARS}\\-@]|\\.[A-Za-z0-9])`,
  "gu",
);

export const email = simple(
  "EMAIL",
  "email",
  EMAIL_PATTERN,
  () => S.EMAIL,
  (value) => value.toLowerCase(),
);

/** In the same order as kavach.detectors.ALL_DETECTORS. */
export const ALL_DETECTORS: readonly Detector[] = [
  aadhaar,
  pan,
  upi,
  ifsc,
  bankAccount,
  phone,
  gstin,
  email,
];
