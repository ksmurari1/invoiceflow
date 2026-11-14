import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ApiError } from "@/services/api";
import { acme } from "@/test/utils";

import { InvoiceForm } from "./InvoiceForm";
import type { InvoiceFormValues } from "./invoiceFormModel";

const initialValues: InvoiceFormValues = {
  clientId: "",
  issueDate: "2026-03-01",
  dueDate: "2026-03-31",
  currency: "USD",
  taxRate: "0",
  notes: "",
  items: [{ key: 1, description: "", quantity: "1", unitPrice: "" }],
};

function setup(overrides: Partial<InvoiceFormValues> = {}, serverError: unknown = null) {
  const onSubmit = vi.fn();
  render(
    <InvoiceForm
      clients={[acme]}
      initialValues={{ ...initialValues, ...overrides }}
      submitLabel="Create invoice"
      submitting={false}
      serverError={serverError}
      onSubmit={onSubmit}
      onCancel={vi.fn()}
    />,
  );
  return { onSubmit, user: userEvent.setup() };
}

describe("InvoiceForm", () => {
  it("previews totals live with decimal precision", async () => {
    const { user } = setup();

    await user.type(screen.getByLabelText("Line 1 unit price"), "10.00");
    await user.click(screen.getByRole("button", { name: /Add line/ }));
    await user.clear(screen.getByLabelText("Line 2 quantity"));
    await user.type(screen.getByLabelText("Line 2 quantity"), "0.333");
    await user.type(screen.getByLabelText("Line 2 unit price"), "3.00");
    await user.clear(screen.getByLabelText("Tax %"));
    await user.type(screen.getByLabelText("Tax %"), "8.25");

    expect(screen.getByTestId("line-amount-0")).toHaveTextContent("$10.00");
    expect(screen.getByTestId("line-amount-1")).toHaveTextContent("$1.00");
    expect(screen.getByTestId("subtotal")).toHaveTextContent("$11.00");
    expect(screen.getByTestId("tax-amount")).toHaveTextContent("$0.91");
    expect(screen.getByTestId("total")).toHaveTextContent("$11.91");
  });

  it("removes lines but always keeps one", async () => {
    const { user } = setup();
    expect(screen.getByRole("button", { name: "Remove line 1" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: /Add line/ }));
    await user.click(screen.getByRole("button", { name: "Remove line 2" }));

    expect(screen.queryByLabelText("Line 2 description")).not.toBeInTheDocument();
  });

  it("validates before submitting", async () => {
    const { onSubmit, user } = setup({ dueDate: "2026-02-01" });

    await user.click(screen.getByRole("button", { name: "Create invoice" }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText("Choose a client.")).toBeInTheDocument();
    expect(screen.getByText("Due date must be on or after the issue date.")).toBeInTheDocument();
    expect(screen.getByText("Required.")).toBeInTheDocument();
    expect(screen.getByText("Price ≥ 0, up to 2 decimals.")).toBeInTheDocument();
  });

  it("submits money as decimal strings", async () => {
    const { onSubmit, user } = setup();

    await user.selectOptions(screen.getByLabelText(/Client/), "7");
    await user.type(screen.getByLabelText("Line 1 description"), " Design ");
    await user.clear(screen.getByLabelText("Line 1 quantity"));
    await user.type(screen.getByLabelText("Line 1 quantity"), "2.5");
    await user.type(screen.getByLabelText("Line 1 unit price"), "19.99");
    await user.type(screen.getByLabelText("Notes"), "Thanks");
    await user.click(screen.getByRole("button", { name: "Create invoice" }));

    expect(onSubmit).toHaveBeenCalledWith({
      clientId: 7,
      issueDate: "2026-03-01",
      dueDate: "2026-03-31",
      currency: "USD",
      taxRate: "0",
      notes: "Thanks",
      items: [{ description: "Design", quantity: "2.5", unitPrice: "19.99" }],
    });
  });

  it("maps server field errors onto line items", () => {
    setup(
      {},
      new ApiError(422, "validation_error", "Request validation failed.", [
        { field: "items[0].quantity", message: "Input should be greater than 0" },
      ]),
    );

    const list = screen.getByRole("list");
    expect(within(list).getByText("Input should be greater than 0")).toBeInTheDocument();
    expect(screen.getByLabelText("Line 1 quantity")).toHaveAttribute("aria-invalid", "true");
  });
});
