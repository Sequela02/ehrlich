interface Property {
  label: string;
  value: string | number;
  unit?: string;
}

interface PropertyCardProps {
  title: string;
  properties: Property[];
}

export function PropertyCard({ title, properties }: PropertyCardProps) {
  return (
    <div className="rounded-md border border-border p-4">
      <h3 className="mb-3 text-sm font-medium">{title}</h3>
      <dl className="grid grid-cols-2 gap-2">
        {properties.map((p) => (
          <div key={p.label}>
            <dt className="text-xs text-muted-foreground">{p.label}</dt>
            <dd className="text-sm font-medium">
              {p.value}
              {p.unit && <span className="ml-1 text-xs text-muted-foreground">{p.unit}</span>}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
