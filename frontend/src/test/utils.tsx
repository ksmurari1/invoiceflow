import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";

import type { Client, DashboardSummary, Page, User } from "@/types/api";

export const demoUser: User = {
  id: 1,
  email: "demo@invoiceflow.local",
  fullName: "Demo User",
  businessName: "Demo Studio",
  businessAddress: "1 Example Street",
  defaultCurrency: "USD",
  defaultTaxRate: "0.00",
};

export const acme: Client = {
  id: 7,
  name: "Acme Corp",
  email: "billing@acme.example.com",
  company: "Acme",
  address: null,
  notes: null,
  createdAt: "2026-03-01T10:00:00Z",
  updatedAt: "2026-03-01T10:00:00Z",
};

export function page<T>(items: T[]): Page<T> {
  return { items, total: items.length, page: 1, pageSize: 20 };
}

export const emptyDashboard: DashboardSummary = {
  clientCount: 0,
  invoiceCount: 0,
  currencies: [],
  recentInvoices: [],
};

type Handler = (url: URL, init: RequestInit | undefined) => unknown;

/**
 * Replace fetch with a router of `"METHOD /path"` -> handler. Unmatched requests fail the test.
 * Returns the mock so tests can inspect calls.
 */
export function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(typeof input === "string" ? input : input.toString());
    const key = `${init?.method ?? "GET"} ${url.pathname}`;
    const handler = routes[key];
    if (!handler) {
      throw new Error(`Unexpected request: ${key}`);
    }
    return new Response(JSON.stringify(handler(url, init)), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

export function renderWithProviders(ui: ReactElement, { route = "/" }: { route?: string } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
