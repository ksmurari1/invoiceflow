import type { User } from "@/types/api";

import { API_PREFIX, api } from "./api";

export const meService = {
  get: (): Promise<User> => api.get<User>(`${API_PREFIX}/me`),
};
