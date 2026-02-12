import { useQuery } from "@tanstack/react-query";

interface Stats {
  tool_count: number;
  domain_count: number;
  phase_count: number;
  data_source_count: number;
  event_type_count: number;
}

async function fetchStats(): Promise<Stats> {
  const response = await fetch("/api/v1/stats");
  if (!response.ok) {
    throw new Error("Failed to fetch stats");
  }
  return response.json() as Promise<Stats>;
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: fetchStats,
    staleTime: 60_000,
  });
}
