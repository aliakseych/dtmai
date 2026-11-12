import { expect, test } from "bun:test";
import { popoverShift } from "./LanguageSelector";

test("popover already inside the viewport is not moved", () => {
  expect(popoverShift(20, 300, 375)).toBe(0);
});

test("popover overflowing the right edge shifts left by the overflow plus margin", () => {
  expect(popoverShift(200, 480, 375)).toBe(-113);
});

test("popover overflowing the left edge shifts right", () => {
  expect(popoverShift(-40, 240, 375)).toBe(48);
});

test("popover wider than the viewport keeps its left edge visible", () => {
  expect(popoverShift(0, 500, 375)).toBe(8);
});
