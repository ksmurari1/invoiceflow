import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { type InvoiceListParams, invoicesService } from "@/services/invoices";
import type { InvoiceAction, InvoiceInput } from "@/types/api";

export const invoiceKeys = {
  all: ["invoices"] as const,
  list: (params: InvoiceListParams) => ["invoices", "list", params] as const,
  detail: (id: number) => ["invoices", "detail", id] as const,
};

export function useInvoiceList(params: InvoiceListParams) {
  return useQuery({
    queryKey: invoiceKeys.list(params),
    queryFn: () => invoicesService.list(params),
    placeholderData: keepPreviousData,
  });
}

export function useInvoice(id: number) {
  return useQuery({
    queryKey: invoiceKeys.detail(id),
    queryFn: () => invoicesService.get(id),
    enabled: Number.isInteger(id) && id > 0,
  });
}

function useInvalidateInvoiceData() {
  const queryClient = useQueryClient();
  return async () => {
    await queryClient.invalidateQueries({ queryKey: invoiceKeys.all });
    await queryClient.invalidateQueries({ queryKey: ["clients"] });
    await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };
}

export function useSaveInvoice(id?: number) {
  const invalidate = useInvalidateInvoiceData();
  return useMutation({
    mutationFn: (input: InvoiceInput) =>
      id ? invoicesService.update(id, input) : invoicesService.create(input),
    onSuccess: invalidate,
  });
}

export function useInvoiceAction(id: number) {
  const invalidate = useInvalidateInvoiceData();
  return useMutation({
    mutationFn: (action: InvoiceAction) => invoicesService.act(id, action),
    onSuccess: invalidate,
  });
}

export function useDeleteInvoice() {
  const invalidate = useInvalidateInvoiceData();
  return useMutation({
    mutationFn: (id: number) => invoicesService.remove(id),
    onSuccess: invalidate,
  });
}
