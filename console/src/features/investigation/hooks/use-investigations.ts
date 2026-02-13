import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";
import type { InvestigationSummary } from "../types";

export function useInvestigations() {
  return useQuery({
    queryKey: ["investigations"],
    queryFn: () => apiFetch<InvestigationSummary[]>("/investigate"),
    refetchInterval: 10_000,
  });
}
