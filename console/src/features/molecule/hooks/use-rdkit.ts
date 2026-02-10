import { useEffect, useState } from "react";

interface RDKitModule {
  get_mol: (smiles: string) => unknown;
}

export function useRDKit() {
  const [rdkit, setRdkit] = useState<RDKitModule | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function init() {
      try {
        // TODO: Dynamic import of @rdkit/rdkit WASM module
        void setRdkit;
        setLoading(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load RDKit");
        setLoading(false);
      }
    }
    init();
  }, []);

  return { rdkit, loading, error };
}
