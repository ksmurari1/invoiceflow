import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "@/components/layout/AppShell";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PlaceholderPage } from "@/pages/PlaceholderPage";

/** Application routes. The router itself is provided by main.tsx (or by tests). */
export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route
          path="dashboard"
          element={
            <PlaceholderPage
              title="Dashboard"
              description="Outstanding, overdue and paid totals will appear here (Phase 6)."
            />
          }
        />
        <Route
          path="clients"
          element={
            <PlaceholderPage
              title="Clients"
              description="Create and manage the people you bill (Phase 2)."
            />
          }
        />
        <Route
          path="invoices"
          element={
            <PlaceholderPage
              title="Invoices"
              description="Create invoices with line items and download PDFs (Phases 3–5)."
            />
          }
        />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
