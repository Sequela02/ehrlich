import { useQuery } from "@tanstack/react-query";
import type { InvestigationSummary } from "../types";

async function fetchInvestigations(): Promise<InvestigationSummary[]> {
  const response = await fetch("/api/v1/investigate");
  if (!response.ok) {
    throw new Error("Failed to fetch investigations");
  }
  return response.json() as Promise<InvestigationSummary[]>;
}

export function useInvestigations() {
  return useQuery({
    queryKey: ["investigations"],
    queryFn: fetchInvestigations,
    refetchInterval: 10_000,
  });
}
