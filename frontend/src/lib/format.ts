import type { IsoDate } from "@/types/api";

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

function parseIsoDate(value: IsoDate): Date | null {
  const match = ISO_DATE.exec(value);
  if (!match) {
    return null;
  }
  const [, y, m, d] = match;
  // Local-time date, so the calendar day never shifts across time zones.
  return new Date(Number(y), Number(m) - 1, Number(d));
}

function toIsoDate(date: Date): IsoDate {
  const y = String(date.getFullYear());
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Today's local date as YYYY-MM-DD. */
export function todayIso(): IsoDate {
  return toIsoDate(new Date());
}

/** Add calendar days to an ISO date. Returns the input unchanged if it is not a valid date. */
export function addDaysIso(value: IsoDate, days: number): IsoDate {
  const date = parseIsoDate(value);
  if (!date) {
    return value;
  }
  date.setDate(date.getDate() + days);
  return toIsoDate(date);
}

/** Format an ISO date for display, e.g. "2026-03-01" -> "Mar 1, 2026". */
export function formatDate(value: IsoDate, locale = "en-US"): string {
  const date = parseIsoDate(value);
  if (!date) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(date);
}

/** Display a decimal string without trailing zeros, e.g. "2.500" -> "2.5", "3.000" -> "3". */
export function formatQuantity(value: string): string {
  return value.includes(".") ? value.replace(/0+$/, "").replace(/\.$/, "") : value;
}
