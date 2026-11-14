import { ApiError } from "@/services/api";

/** User-facing message for any thrown value. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}

/** Field-level errors from an API validation error, keyed by field path (e.g. "items[0].quantity"). */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) {
    return {};
  }
  const result: Record<string, string> = {};
  for (const { field, message } of error.fields) {
    if (field && !(field in result)) {
      result[field] = message;
    }
  }
  return result;
}
