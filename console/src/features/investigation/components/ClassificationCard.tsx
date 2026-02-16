import { Badge } from "@/shared/components/ui/badge";
import type { DomainDisplayConfig } from "../types";

interface ClassificationCardProps {
  domainConfig: DomainDisplayConfig | null;
}

export function ClassificationCard({ domainConfig }: ClassificationCardProps) {
  if (!domainConfig) {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground/60">
        <div className="h-2 w-2 animate-pulse rounded-full bg-primary/40" />
        Classifying research domain...
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Badge variant="outline" className="text-xs">
        {domainConfig.display_name}
      </Badge>
      {domainConfig.domains && domainConfig.domains.length > 1 && (
        <span className="text-[10px] text-muted-foreground/60">
          Multi-domain: {domainConfig.domains.map((d) => d.display_name).join(" + ")}
        </span>
      )}
    </div>
  );
}
