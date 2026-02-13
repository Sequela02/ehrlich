import { useReducedMotion } from "motion/react";

/**
 * Returns animation config that respects prefers-reduced-motion.
 * When reduced motion is preferred, animations are skipped entirely.
 */
export function useAnimationConfig() {
  const reduced = useReducedMotion();

  return {
    /** Pass as `initial` prop -- `false` skips the initial animation state */
    initial: reduced ? (false as const) : undefined,
    /** Pass as `transition` prop -- duration 0 makes animations instant */
    transition: reduced ? ({ duration: 0 } as const) : undefined,
    /** Whether reduced motion is active */
    reduced: !!reduced,
  };
}
