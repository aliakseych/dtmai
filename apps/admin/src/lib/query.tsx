"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ToastProvider } from "@dtmai/ui";
import { ApiError } from "@dtmai/api-client";
import { AuthProvider } from "./auth";

export function Providers({ children }: { children: ReactNode }) {
  const [qc] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchOnWindowFocus: false,
            retry: (n, e) => !(e instanceof ApiError && e.status < 500) && n < 2,
          },
        },
      }),
  );
  return (
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>{children}</AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
