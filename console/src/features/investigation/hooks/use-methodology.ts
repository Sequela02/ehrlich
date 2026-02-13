import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";

interface ScoreDefinition {
  key: string;
  label: string;
  format_spec: string;
  higher_is_better: boolean;
}

interface DomainInfo {
  name: string;
  display_name: string;
  tool_count: number;
  score_definitions: ScoreDefinition[];
  hypothesis_types: string[];
  categories: string[];
}

interface ToolInfo {
  name: string;
  description: string;
  tags: string[];
}

interface ToolGroup {
  context: string;
  tools: ToolInfo[];
}

interface Phase {
  number: number;
  name: string;
  description: string;
  model: string;
}

interface ModelInfo {
  role: string;
  model_id: string;
  purpose: string;
}

interface DataSource {
  name: string;
  url: string;
  purpose: string;
  auth: string;
  context: string;
}

export interface Methodology {
  phases: Phase[];
  domains: DomainInfo[];
  tools: ToolGroup[];
  data_sources: DataSource[];
  models: ModelInfo[];
}

export function useMethodology() {
  return useQuery({
    queryKey: ["methodology"],
    queryFn: () => apiFetch<Methodology>("/methodology"),
    staleTime: 5 * 60_000,
  });
}
