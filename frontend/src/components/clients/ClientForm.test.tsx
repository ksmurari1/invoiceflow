import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/services/api";

import { ClientForm } from "./ClientForm";

function setup(serverError: unknown = null) {
  const onSubmit = vi.fn();
  render(
    <ClientForm
      submitLabel="Create client"
      submitting={false}
      serverError={serverError}
      onSubmit={onSubmit}
      onCancel={vi.fn()}
    />,
  );
  return { onSubmit, user: userEvent.setup() };
}

describe("ClientForm", () => {
  it("requires name and a valid email", async () => {
    const { onSubmit, user } = setup();

    await user.click(screen.getByRole("button", { name: "Create client" }));

    expect(screen.getByText("Name is required.")).toBeInTheDocument();
    expect(screen.getByText("Email is required.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/Email/), "nope");
    await user.click(screen.getByRole("button", { name: "Create client" }));
    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits trimmed values with blank optionals as null", async () => {
    const { onSubmit, user } = setup();

    await user.type(screen.getByLabelText(/Name/), "  Globex ");
    await user.type(screen.getByLabelText(/Email/), "ap@globex.example.com");
    await user.type(screen.getByLabelText("Company"), "   ");
    await user.click(screen.getByRole("button", { name: "Create client" }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Globex",
      email: "ap@globex.example.com",
      company: null,
      address: null,
      notes: null,
    });
  });

  it("shows server field errors next to the field", () => {
    setup(
      new ApiError(422, "validation_error", "Request validation failed.", [
        { field: "email", message: "value is not a valid email address" },
      ]),
    );

    expect(screen.getByLabelText(/Email/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByText("value is not a valid email address")).toBeInTheDocument();
  });
});
