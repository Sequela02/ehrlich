import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";

interface Stats {
  tool_count: number;
  domain_count: number;
  phase_count: number;
  data_source_count: number;
  event_type_count: number;
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => apiFetch<Stats>("/stats"),
    staleTime: 60_000,
  });
}
