/** Checksums, mirroring kavach/validators/. Errors never echo the input. */

// --- Verhoeff (Aadhaar check digit) ------------------------------------------
// https://en.wikipedia.org/wiki/Verhoeff_algorithm

const D = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
  [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
  [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
  [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
  [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
  [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
  [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
  [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
  [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
] as const;

const P = [
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
  [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
  [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
  [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
  [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
  [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
  [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
  [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
] as const;

const INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9] as const;

function digitsOf(value: string): number[] {
  if (!/^[0-9]+$/.test(value)) {
    throw new RangeError("Verhoeff input must be a non-empty string of ASCII digits");
  }
  return [...value].reverse().map(Number);
}

function step(c: number, i: number, digit: number): number {
  return D[c]![P[i % 8]![digit]!]!;
}

export function verhoeffIsValid(value: string): boolean {
  return digitsOf(value).reduce((c, digit, i) => step(c, i, digit), 0) === 0;
}

export function verhoeffCheckDigit(value: string): string {
  const c = digitsOf(value).reduce((acc, digit, i) => step(acc, i + 1, digit), 0);
  return String(INV[c]);
}

// --- GSTIN check character -----------------------------------------------------
// https://en.wikipedia.org/wiki/Goods_and_Services_Tax_(India)#GSTIN

const CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";

function base36(value: string, length: number): string {
  const upper = value.toUpperCase();
  if ([...upper].length !== length || [...upper].some((ch) => !CHARSET.includes(ch))) {
    throw new RangeError(`expected ${length} characters from 0-9 and A-Z`);
  }
  return upper;
}

export function gstinCheckChar(first14: string): string {
  let total = 0;
  [...base36(first14, 14)].forEach((ch, i) => {
    const product = CHARSET.indexOf(ch) * (i % 2 ? 2 : 1);
    total += Math.floor(product / 36) + (product % 36);
  });
  return CHARSET[(36 - (total % 36)) % 36]!;
}

export function gstinIsValid(gstin: string): boolean {
  const upper = base36(gstin, 15);
  return gstinCheckChar(upper.slice(0, 14)) === upper[14];
}
