/** Typed access to rules.json, which is generated from the Python package. */

import data from "./rules.json" with { type: "json" };
import type { EntityType } from "./types.ts";

export interface Rules {
  entityTypes: EntityType[];
  keywords: Record<EntityType, string[]>;
  notPiiLabels: string[];
  contextWindowBefore: number;
  contextWindowAfter: number;
  labelWindow: number;
  defaultThreshold: number;
  contextBoost: number;
  notPiiLabelPenalty: number;
  numericEntities: EntityType[];
  specificity: EntityType[];
  placeholderMaxLength: number;
  systemPrompt: string;
  scores: {
    AADHAAR: number;
    PAN: number;
    UPI_KNOWN_HANDLE: number;
    UPI_UNKNOWN_HANDLE: number;
    IFSC_KNOWN_BANK: number;
    IFSC_UNKNOWN_BANK: number;
    BANK_ACCOUNT: number;
    PHONE_INTERNATIONAL: number;
    PHONE: number;
    GSTIN: number;
    EMAIL: number;
  };
  panHolderTypes: string;
  gstinStateCodes: string[];
  upiKnownHandles: string[];
  ifscKnownBankCodes: string[];
}

export const RULES = data as unknown as Rules;
