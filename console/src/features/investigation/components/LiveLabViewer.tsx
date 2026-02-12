import { useEffect, useRef, useState } from "react";
import { FlaskConical } from "lucide-react";
import type { GLViewer } from "3dmol";
import type { Experiment, SSEEvent } from "../types";
import { buildSceneUpdates, type SceneAction } from "../lib/scene-builder";

interface LiveLabViewerProps {
  events: SSEEvent[];
  completed: boolean;
  experiments?: Experiment[];
}

export function LiveLabViewer({ events, completed, experiments }: LiveLabViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<GLViewer | null>(null);
  const processedRef = useRef(0);
  const seenSmilesRef = useRef(new Set<string>());
  const [ready, setReady] = useState(false);
  const [hasContent, setHasContent] = useState(false);
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    if (el.offsetWidth === 0 || el.offsetHeight === 0) return;
    let cancelled = false;

    import("3dmol").then((mod) => {
      if (cancelled || !containerRef.current) return;
      if (containerRef.current.offsetWidth === 0) return;
      const viewer = mod.createViewer(containerRef.current, {
        backgroundColor: "#0f1219",
      });
      viewerRef.current = viewer;
      viewer.render();
      setReady(true);
    });

    return () => {
      cancelled = true;
      if (viewerRef.current) {
        viewerRef.current.clear();
        viewerRef.current = null;
      }
    };
  }, []);

  // Reset viewer when switching experiments
  useEffect(() => {
    if (!viewerRef.current) return;
    viewerRef.current.clear();
    viewerRef.current.render();
    processedRef.current = 0;
    seenSmilesRef.current = new Set();
    setHasContent(false);
  }, [activeExperimentId]);

  useEffect(() => {
    if (!ready || !viewerRef.current) return;

    const viewer = viewerRef.current;
    const seen = seenSmilesRef.current;
    const filteredEvents = activeExperimentId
      ? events.filter((e) => (e.data as Record<string, unknown>).experiment_id === activeExperimentId)
      : events;
    const newEvents = filteredEvents.slice(processedRef.current);
    processedRef.current = filteredEvents.length;

    for (const event of newEvents) {
      const actions = buildSceneUpdates({ type: event.event, data: event.data });
      for (const action of actions) {
        if (action.type === "addLigand" && seen.has(action.smiles)) continue;
        if (action.type === "addLigand") seen.add(action.smiles);
        applyAction(viewer, action);
        setHasContent(true);
      }
    }

    if (newEvents.length > 0) {
      viewer.render();
    }
  }, [events, ready, activeExperimentId]);

  return (
    <div className="relative overflow-hidden rounded-lg border border-border">
      {experiments && experiments.length > 0 && (
        <div className="flex items-center gap-2 border-b border-border p-2">
          <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            Experiment:
          </span>
          <select
            value={activeExperimentId ?? "all"}
            onChange={(e) => setActiveExperimentId(e.target.value === "all" ? null : e.target.value)}
            className="rounded-md border border-border bg-surface px-2 py-1 text-xs text-foreground"
          >
            <option value="all">All</option>
            {experiments.map((exp) => (
              <option key={exp.id} value={exp.id}>
                {exp.description.slice(0, 50)}
              </option>
            ))}
          </select>
        </div>
      )}
      <div
        ref={containerRef}
        style={{ width: "100%", height: 400, position: "relative" }}
        className="bg-[#0f1219]"
      />
      {!hasContent && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <FlaskConical className="h-8 w-8 text-muted-foreground/30" />
          <p className="text-sm text-muted-foreground/50">
            {completed
              ? "No molecular data was visualized"
              : "Waiting for molecular data..."}
          </p>
        </div>
      )}
    </div>
  );
}

function addLigandModel(viewer: GLViewer, molblock: string, color?: string): void {
  viewer.addModel(molblock, "sdf");
  const scheme = color
    ? { prop: "elem", map: { C: color } }
    : "greenCarbon";
  viewer.setStyle(
    { model: -1 },
    { stick: { colorscheme: scheme as string } },
  );
  viewer.zoomTo({ model: -1 });
  viewer.render();
}

function applyAction(viewer: GLViewer, action: SceneAction): void {
  switch (action.type) {
    case "addProtein": {
      const url = `https://files.rcsb.org/download/${action.pdbId}.pdb`;
      fetch(url)
        .then((r) => r.text())
        .then((pdb) => {
          viewer.addModel(pdb, "pdb");
          viewer.setStyle({ model: -1 }, { cartoon: { color: "spectrum" } });
          viewer.zoomTo();
          viewer.render();
        })
        .catch(() => {});
      break;
    }
    case "addLigand": {
      if (action.molblock) {
        addLigandModel(viewer, action.molblock, action.color);
      } else {
        fetch(`/api/v1/molecule/conformer?smiles=${encodeURIComponent(action.smiles)}`)
          .then((r) => r.json())
          .then((data: { mol_block?: string }) => {
            if (data.mol_block) {
              addLigandModel(viewer, data.mol_block, action.color);
            }
          })
          .catch(() => {});
      }
      break;
    }
    case "addLabel": {
      (viewer as unknown as { addLabel: (text: string, opts: Record<string, unknown>) => void }).addLabel(action.text, {
        position: action.position,
        fontSize: 14,
        fontColor: action.color ?? "#ffffff",
        backgroundColor: "#000000",
        backgroundOpacity: 0.7,
      });
      break;
    }
    case "colorByScore": {
      const addLabelFn = (viewer as unknown as { addLabel: (text: string, opts: Record<string, unknown>) => void }).addLabel.bind(viewer);
      for (const { score } of action.scores) {
        const color = score > 0.7 ? "#22c55e" : score > 0.4 ? "#f97316" : "#ef4444";
        addLabelFn(`${score.toFixed(2)}`, {
          position: { x: 0, y: 0, z: 0 },
          fontSize: 12,
          fontColor: color,
          backgroundColor: "#000000",
          backgroundOpacity: 0.7,
        });
      }
      break;
    }
    case "zoomTo":
      viewer.zoomTo(action.selection);
      break;
    case "highlight":
      break;
    case "clear":
      viewer.clear();
      break;
  }
}
