import { FileText, LayoutDashboard, type LucideIcon, Users } from "lucide-react";
import { NavLink } from "react-router";

import { useMe } from "@/hooks/useMe";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/clients", label: "Clients", icon: Users },
  { to: "/invoices", label: "Invoices", icon: FileText },
];

export function Sidebar() {
  const { data: me } = useMe();
  return (
    <aside className="flex flex-col border-b bg-sidebar text-sidebar-foreground md:w-60 md:shrink-0 md:border-r md:border-b-0">
      <div className="flex h-14 items-center px-4 text-lg font-semibold tracking-tight">
        InvoiceFlow
      </div>
      <nav aria-label="Main" className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col md:pb-0">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
              )
            }
          >
            <Icon className="size-4" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto hidden px-4 py-4 text-xs text-muted-foreground md:block">
        <p className="font-medium text-sidebar-foreground">
          {me?.businessName ?? me?.fullName ?? "…"}
        </p>
        <p>Local demo mode</p>
      </div>
    </aside>
  );
}
