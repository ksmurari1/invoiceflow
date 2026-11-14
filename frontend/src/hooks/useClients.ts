import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { type ClientListParams, clientsService } from "@/services/clients";
import type { ClientInput } from "@/types/api";

export const clientKeys = {
  all: ["clients"] as const,
  list: (params: ClientListParams) => ["clients", "list", params] as const,
  detail: (id: number) => ["clients", "detail", id] as const,
};

export function useClientList(params: ClientListParams) {
  return useQuery({
    queryKey: clientKeys.list(params),
    queryFn: () => clientsService.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useClient(id: number) {
  return useQuery({
    queryKey: clientKeys.detail(id),
    queryFn: () => clientsService.get(id),
    enabled: Number.isInteger(id) && id > 0,
  });
}

export function useSaveClient(id?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ClientInput) =>
      id ? clientsService.update(id, input) : clientsService.create(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clientKeys.all });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => clientsService.remove(id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: clientKeys.all });
      await queryClient.invalidateQueries({ queryKey: ["invoices"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
