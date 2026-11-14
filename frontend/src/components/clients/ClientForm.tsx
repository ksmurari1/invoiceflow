import { type FormEvent, useState } from "react";

import { ErrorAlert } from "@/components/common/Feedback";
import { FormField } from "@/components/common/FormField";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { fieldErrors } from "@/lib/errors";
import { fieldA11y, looksLikeEmail, optionalText } from "@/lib/forms";
import type { Client, ClientInput } from "@/types/api";

interface ClientFormValues {
  name: string;
  email: string;
  company: string;
  address: string;
  notes: string;
}

interface ClientFormProps {
  initial?: Client;
  submitLabel: string;
  submitting: boolean;
  serverError: unknown;
  onSubmit: (input: ClientInput) => void;
  onCancel: () => void;
}

function toValues(client?: Client): ClientFormValues {
  return {
    name: client?.name ?? "",
    email: client?.email ?? "",
    company: client?.company ?? "",
    address: client?.address ?? "",
    notes: client?.notes ?? "",
  };
}

function validate(values: ClientFormValues): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!values.name.trim()) errors.name = "Name is required.";
  if (!values.email.trim()) errors.email = "Email is required.";
  else if (!looksLikeEmail(values.email)) errors.email = "Enter a valid email address.";
  return errors;
}

export function ClientForm({
  initial,
  submitLabel,
  submitting,
  serverError,
  onSubmit,
  onCancel,
}: ClientFormProps) {
  const [values, setValues] = useState<ClientFormValues>(() => toValues(initial));
  const [clientErrors, setClientErrors] = useState<Record<string, string>>({});
  const errors = { ...fieldErrors(serverError), ...clientErrors };

  const set = (field: keyof ClientFormValues) => (value: string) =>
    setValues((current) => ({ ...current, [field]: value }));

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const found = validate(values);
    setClientErrors(found);
    if (Object.keys(found).length > 0) return;
    onSubmit({
      name: values.name.trim(),
      email: values.email.trim(),
      company: optionalText(values.company),
      address: optionalText(values.address),
      notes: optionalText(values.notes),
    });
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">
      {serverError && Object.keys(fieldErrors(serverError)).length === 0 ? (
        <ErrorAlert error={serverError} title="Could not save client" />
      ) : null}
      <div className="grid gap-5 sm:grid-cols-2">
        <FormField id="client-name" label="Name" required error={errors.name}>
          <Input
            {...fieldA11y("client-name", errors.name)}
            value={values.name}
            onChange={(e) => set("name")(e.target.value)}
            autoComplete="off"
            maxLength={200}
          />
        </FormField>
        <FormField id="client-email" label="Email" required error={errors.email}>
          <Input
            {...fieldA11y("client-email", errors.email)}
            type="email"
            value={values.email}
            onChange={(e) => set("email")(e.target.value)}
            autoComplete="off"
          />
        </FormField>
        <FormField id="client-company" label="Company" error={errors.company}>
          <Input
            {...fieldA11y("client-company", errors.company)}
            value={values.company}
            onChange={(e) => set("company")(e.target.value)}
            maxLength={200}
          />
        </FormField>
        <FormField
          id="client-address"
          label="Address"
          error={errors.address}
          className="sm:col-span-2"
        >
          <Textarea
            {...fieldA11y("client-address", errors.address)}
            value={values.address}
            onChange={(e) => set("address")(e.target.value)}
            rows={3}
            maxLength={1000}
          />
        </FormField>
        <FormField id="client-notes" label="Notes" error={errors.notes} className="sm:col-span-2">
          <Textarea
            {...fieldA11y("client-notes", errors.notes)}
            value={values.notes}
            onChange={(e) => set("notes")(e.target.value)}
            rows={3}
            maxLength={5000}
          />
        </FormField>
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Saving…" : submitLabel}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
