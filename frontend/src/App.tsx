import { Navigate, Route, Routes } from "react-router";

import { AppShell } from "@/components/layout/AppShell";
import { ClientDetailPage } from "@/pages/clients/ClientDetailPage";
import { ClientFormPage } from "@/pages/clients/ClientFormPage";
import { ClientListPage } from "@/pages/clients/ClientListPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { InvoiceDetailPage } from "@/pages/invoices/InvoiceDetailPage";
import { InvoiceFormPage } from "@/pages/invoices/InvoiceFormPage";
import { InvoiceListPage } from "@/pages/invoices/InvoiceListPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

/** Application routes. The router and query client are provided by main.tsx (or by tests). */
export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="clients" element={<ClientListPage />} />
        <Route path="clients/new" element={<ClientFormPage />} />
        <Route path="clients/:id" element={<ClientDetailPage />} />
        <Route path="clients/:id/edit" element={<ClientFormPage />} />
        <Route path="invoices" element={<InvoiceListPage />} />
        <Route path="invoices/new" element={<InvoiceFormPage />} />
        <Route path="invoices/:id" element={<InvoiceDetailPage />} />
        <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
