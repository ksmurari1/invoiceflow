import type { Currency } from "@/types/api";

/** Currencies the backend accepts (all use 2 decimal places). */
export const CURRENCIES: readonly Currency[] = ["USD", "EUR", "GBP", "CAD", "AUD", "INR"];

export const DEFAULT_PAYMENT_DAYS = 30;
