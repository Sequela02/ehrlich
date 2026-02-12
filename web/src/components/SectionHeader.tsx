export function SectionHeader({ title }: { title: string }) {
  return (
    <h2 className="font-mono uppercase tracking-[0.12em] text-sm text-foreground mb-12 border-l-2 border-primary pl-4">
      {title}
    </h2>
  );
}
