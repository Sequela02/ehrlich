import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "@/shared/lib/api";
import type { InvestigationRequest, InvestigationResponse } from "../types";

export function useInvestigation() {
  return useMutation({
    mutationFn: (request: InvestigationRequest) =>
      apiFetch<InvestigationResponse>("/investigate", {
        method: "POST",
        body: JSON.stringify(request),
      }),
  });
}
