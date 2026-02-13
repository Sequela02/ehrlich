import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";

interface CreditBalance {
  credits: number;
  is_byok: boolean;
}

export function useCredits() {
  return useQuery({
    queryKey: ["credits"],
    queryFn: () => apiFetch<CreditBalance>("/credits/balance"),
    staleTime: 10_000,
  });
}
