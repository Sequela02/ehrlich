import { useQuery } from "@tanstack/react-query";
import type { InvestigationDetail } from "../types";

async function fetchDetail(id: string): Promise<InvestigationDetail> {
  const response = await fetch(`/api/v1/investigate/${id}`);
  if (!response.ok) {
    throw new Error("Failed to fetch investigation detail");
  }
  return response.json() as Promise<InvestigationDetail>;
}

export function useInvestigationDetail(id: string | null) {
  return useQuery({
    queryKey: ["investigation-detail", id],
    queryFn: () => fetchDetail(id!),
    enabled: !!id,
  });
}
