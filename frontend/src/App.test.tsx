import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { App } from "./App";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App shell", () => {
  it("redirects / to the dashboard", () => {
    renderAt("/");
    expect(screen.getByRole("heading", { level: 1, name: "Dashboard" })).toBeInTheDocument();
  });

  it("shows the main navigation", () => {
    renderAt("/dashboard");
    const nav = screen.getByRole("navigation", { name: "Main" });
    expect(nav).toHaveTextContent("Dashboard");
    expect(nav).toHaveTextContent("Clients");
    expect(nav).toHaveTextContent("Invoices");
  });

  it("navigates between sections", async () => {
    const user = userEvent.setup();
    renderAt("/dashboard");

    await user.click(screen.getByRole("link", { name: "Clients" }));

    expect(screen.getByRole("heading", { level: 1, name: "Clients" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Clients" })).toHaveAttribute("aria-current", "page");
  });

  it("shows a not-found page for unknown routes", () => {
    renderAt("/nope");
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
  });
});
