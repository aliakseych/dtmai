import { describe, expect, test } from "bun:test";
import { LOCALES, MESSAGES } from "../src/locales";

const base = Object.keys(MESSAGES["uz-Latn"]).sort();
const placeholders = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort().join(",");

describe("locale parity", () => {
  for (const l of LOCALES) {
    test(`${l} has exactly the same keys`, () => {
      expect(Object.keys(MESSAGES[l]).sort()).toEqual(base);
    });
    test(`${l} has no empty values and same placeholders`, () => {
      for (const k of base) {
        const v = (MESSAGES[l] as Record<string, string>)[k];
        expect(v.trim().length, `${l}:${k}`).toBeGreaterThan(0);
        expect(placeholders(v), `${l}:${k}`).toBe(placeholders((MESSAGES["uz-Latn"] as Record<string, string>)[k]));
      }
    });
  }
});
