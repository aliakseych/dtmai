import { describe, expect, test } from "bun:test";
import { addDays, clampMinutes, datesError, daysBetween, startOfWeek, studyWeekdays, weekdayOf } from "./planDates";

describe("planDates", () => {
  test("weekday is Monday-based", () => {
    expect(weekdayOf("2027-07-25")).toBe(6); // Sunday
    expect(weekdayOf("2027-07-26")).toBe(0); // Monday
  });
  test("startOfWeek returns Monday", () => {
    expect(startOfWeek("2027-07-25")).toBe("2027-07-19");
    expect(startOfWeek("2027-07-19")).toBe("2027-07-19");
  });
  test("addDays crosses months and DST", () => {
    expect(addDays("2027-01-31", 1)).toBe("2027-02-01");
    expect(addDays("2027-03-27", 2)).toBe("2027-03-29");
    expect(daysBetween("2027-01-01", "2027-07-25")).toBe(205);
  });
  test("datesError enforces start and 14-day lead", () => {
    expect(datesError("2027-01-10", "2027-01-09", "2027-07-25")).toBe("start_past");
    expect(datesError("2027-01-10", "2027-01-10", "2027-01-23")).toBe("exam_too_soon");
    expect(datesError("2027-01-10", "2027-01-10", "2027-01-24")).toBeNull();
    expect(datesError("2027-01-10", "", "2027-07-25")).toBe("exam_too_soon");
  });
  test("studyWeekdays drops the rest day", () => {
    expect(studyWeekdays([6, 0, 2], 6)).toEqual([0, 2]);
    expect(studyWeekdays([0, 1], null)).toEqual([0, 1]);
  });
  test("clampMinutes bounds 10..150", () => {
    expect(clampMinutes(5)).toBe(10);
    expect(clampMinutes(400)).toBe(150);
    expect(clampMinutes(44.6)).toBe(45);
  });
});
