import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { acme, demoUser, emptyDashboard, mockApi, page, renderWithProviders } from "@/test/utils";

import { App } from "./App";

describe("App shell", () => {
  beforeEach(() => {
    mockApi({
      "GET /api/v1/me": () => demoUser,
      "GET /api/v1/dashboard/summary": () => emptyDashboard,
      "GET /api/v1/clients": () => page([acme]),
      "GET /api/v1/invoices": () => page([]),
    });
  });

  it("redirects / to the dashboard and shows onboarding", async () => {
    renderWithProviders(<App />, { route: "/" });

    expect(await screen.findByRole("heading", { level: 1, name: "Dashboard" })).toBeInTheDocument();
    expect(await screen.findByText("Welcome to InvoiceFlow")).toBeInTheDocument();
    expect(await screen.findByText("Demo Studio")).toBeInTheDocument();
  });

  it("navigates to clients and lists them", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/dashboard" });

    await user.click(screen.getByRole("link", { name: "Clients" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Clients" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Acme Corp" })).toHaveAttribute(
      "href",
      "/clients/7",
    );
  });

  it("shows an empty invoice list", async () => {
    renderWithProviders(<App />, { route: "/invoices" });

    expect(await screen.findByText("No invoices yet")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "All" })).toHaveAttribute("aria-selected", "true");
  });

  it("shows a not-found page for unknown routes", () => {
    renderWithProviders(<App />, { route: "/nope" });
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });
});
