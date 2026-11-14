import type { ApiErrorBody, ApiErrorField } from "@/types/api";

const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
export const API_PREFIX = "/api/v1";

/** An error returned by the API (or a network failure, with status 0). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: ApiErrorField[];

  constructor(status: number, code: string, message: string, fields: ApiErrorField[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

type TokenProvider = () => string | null;
type UnauthorizedHandler = () => void;

let getToken: TokenProvider = () => null;
let onUnauthorized: UnauthorizedHandler | null = null;

/** Register how the client obtains the current access token (set by the auth layer). */
export function setTokenProvider(provider: TokenProvider): void {
  getToken = provider;
}

/** Register a callback invoked when the API answers 401 (e.g. log out and redirect). */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  onUnauthorized = handler;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error: unknown = value.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string"
  );
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

/**
 * Send a request to the InvoiceFlow API and return the parsed JSON body.
 * Throws ApiError for non-2xx responses and network failures.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === "AbortError") {
      throw cause;
    }
    throw new ApiError(0, "network_error", "Could not reach the server. Is the API running?");
  }

  const data = await readJson(response);

  if (!response.ok) {
    if (response.status === 401 && onUnauthorized) {
      onUnauthorized();
    }
    if (isApiErrorBody(data)) {
      const { code, message, fields } = data.error;
      throw new ApiError(response.status, code, message, Array.isArray(fields) ? fields : []);
    }
    throw new ApiError(response.status, "http_error", `Request failed (${response.status}).`);
  }

  return data as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => apiRequest<T>(path, { signal }),
  post: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "POST", body }),
  put: <T>(path: string, body: unknown) => apiRequest<T>(path, { method: "PUT", body }),
  delete: <T = null>(path: string) => apiRequest<T>(path, { method: "DELETE" }),
};
