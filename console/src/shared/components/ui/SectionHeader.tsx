import type { LucideIcon } from "lucide-react";

interface SectionHeaderProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function SectionHeader({ icon: Icon, title, description }: SectionHeaderProps) {
  return (
    <div>
      <h3 className="flex items-center gap-2 border-l-2 border-primary pl-4 font-mono text-xs font-medium uppercase tracking-[0.08em] text-muted-foreground">
        <Icon className="h-3.5 w-3.5 text-primary" />
        {title}
      </h3>
      <p className="mt-1 pl-6 text-xs leading-relaxed text-muted-foreground/60">
        {description}
      </p>
    </div>
  );
}
