import type { DashboardSummary } from "@/types/api";

import { API_PREFIX, api } from "./api";

export const dashboardService = {
  summary: (): Promise<DashboardSummary> =>
    api.get<DashboardSummary>(`${API_PREFIX}/dashboard/summary`),
};
