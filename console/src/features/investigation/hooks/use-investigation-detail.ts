import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";
import type { InvestigationDetail } from "../types";

export function useInvestigationDetail(id: string | null) {
  return useQuery({
    queryKey: ["investigation-detail", id],
    queryFn: () => apiFetch<InvestigationDetail>(`/investigate/${id}`),
    enabled: !!id,
  });
}
