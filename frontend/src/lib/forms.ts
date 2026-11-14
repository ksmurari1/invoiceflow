/** Props that wire a form control to its FormField error message. */
export function fieldA11y(id: string, error?: string) {
  return {
    id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": error ? `${id}-error` : undefined,
  };
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Light client-side email check; the server performs the authoritative validation. */
export function looksLikeEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

/** Trimmed text, or null when empty (for optional API fields). */
export function optionalText(value: string): string | null {
  const text = value.trim();
  return text ? text : null;
}
