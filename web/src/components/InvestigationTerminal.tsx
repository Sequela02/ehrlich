import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  INVESTIGATION_LINES,
  type LineVariant,
} from "@/lib/investigation-lines";

const VARIANT_STYLES: Record<LineVariant, string> = {
  command: "text-primary font-bold",
  query: "text-foreground/80",
  phase: "text-muted-foreground",
  hypothesis: "text-accent",
  tool: "text-muted-foreground/60",
  finding: "text-primary font-medium terminal-finding",
  status: "text-primary font-bold",
  blank: "",
};

export function InvestigationTerminal({
  autoPlay = true,
  onComplete,
}: {
  autoPlay?: boolean;
  onComplete?: () => void;
}) {
  const reduced = useReducedMotion();
  const [visibleCount, setVisibleCount] = useState(reduced ? INVESTIGATION_LINES.length : 0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!autoPlay || reduced) return;

    let elapsed = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    for (let i = 0; i < INVESTIGATION_LINES.length; i++) {
      elapsed += INVESTIGATION_LINES[i].delay;
      const timer = setTimeout(() => {
        setVisibleCount(i + 1);
        if (i === INVESTIGATION_LINES.length - 1) {
          onComplete?.();
        }
      }, elapsed);
      timers.push(timer);
    }

    timersRef.current = timers;
    return () => timers.forEach(clearTimeout);
  }, [autoPlay, reduced, onComplete]);

  // Auto-scroll terminal body as lines appear
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [visibleCount]);

  const lines = INVESTIGATION_LINES.slice(0, visibleCount);
  const isComplete = visibleCount >= INVESTIGATION_LINES.length;

  return (
    <div className="terminal-frame">
      <div className="terminal-header">
        <span className="terminal-dot" />
        <span className="terminal-dot" />
        <span className="terminal-dot" />
        <span className="ml-3 font-mono text-[10px] text-muted-foreground/50 uppercase tracking-wider">
          ehrlich
        </span>
      </div>
      <div ref={bodyRef} className="terminal-body">
        {lines.map((line, i) =>
          line.variant === "blank" ? (
            <div key={i} className="h-4" />
          ) : (
            <motion.div
              key={i}
              initial={reduced ? false : { opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
              className={`font-mono text-xs leading-relaxed whitespace-pre ${VARIANT_STYLES[line.variant]}`}
            >
              {line.variant === "phase" && (
                <span className="text-primary">{line.text.slice(0, 7)}</span>
              )}
              {line.variant === "phase" ? line.text.slice(7) : line.text}
            </motion.div>
          ),
        )}
        {!isComplete && visibleCount > 0 && (
          <span className="terminal-cursor" />
        )}
      </div>
    </div>
  );
}
