"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { CONTRACT_ADDRESS } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: 1, staleTime: 0, gcTime: 0 },
        },
      })
  );

  useEffect(() => {
    const onAuthChange = () => {
      queryClient.clear();
      queryClient.invalidateQueries();
    };

    const contractKey = "slashsure-contract-address";
    const previousContract = localStorage.getItem(contractKey);
    if (previousContract !== CONTRACT_ADDRESS) {
      queryClient.clear();
      queryClient.invalidateQueries();
      localStorage.setItem(contractKey, CONTRACT_ADDRESS);
    }

    window.addEventListener("slashsure-auth-change", onAuthChange);
    return () => window.removeEventListener("slashsure-auth-change", onAuthChange);
  }, [queryClient]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
