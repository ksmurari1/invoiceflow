import { Outlet } from "react-router";

import { Sidebar } from "./Sidebar";

/** Authenticated application layout: navigation plus the routed page. */
export function AppShell() {
  return (
    <div className="flex min-h-svh flex-col md:flex-row">
      <Sidebar />
      <main className="flex-1 p-4 md:p-8">
        <Outlet />
      </main>
    </div>
  );
}
