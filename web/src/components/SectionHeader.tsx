import { useRef } from "react";
import { motion, useInView } from "motion/react";

export function SectionHeader({ title }: { title: string }) {
  const ref = useRef<HTMLHeadingElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-40px" });

  return (
    <motion.h2
      ref={ref}
      initial={{ opacity: 0, x: -12 }}
      animate={isInView ? { opacity: 1, x: 0 } : undefined}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="font-mono uppercase tracking-[0.12em] text-sm text-foreground mb-12 border-l-2 border-primary pl-4"
    >
      {title}
    </motion.h2>
  );
}
