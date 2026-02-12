import { useEffect, useRef } from "react";

/**
 * IntersectionObserver hook for scroll-triggered reveal animations.
 * Adds 'is-visible' class when element enters viewport.
 * One-shot: once visible, stays visible (no re-hide on scroll up).
 */
export function useReveal(threshold = 0.1) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        }
      },
      { threshold, rootMargin: "0px 0px -40px 0px" },
    );

    observer.observe(el);
    return () => observer.unobserve(el);
  }, [threshold]);

  return ref;
}
