import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/services/api";

/** Create the app's query client. Client errors (4xx) are not retried. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status >= 400 && error.status < 500) &&
          failureCount < 1,
      },
    },
  });
}
