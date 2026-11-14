import { useQuery } from "@tanstack/react-query";

import { meService } from "@/services/me";

export function useMe() {
  return useQuery({ queryKey: ["me"], queryFn: meService.get, staleTime: 5 * 60 * 1000 });
}
