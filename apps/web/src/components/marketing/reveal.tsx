"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * Hiện dần khi cuộn tới (reveal-on-scroll). Dùng chung cho mọi section landing.
 * Tôn trọng prefers-reduced-motion qua CSS global (transition-duration ~0).
 */
export function Reveal({
  children,
  delay = 0,
  y = 22,
  className,
  once = true,
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  once?: boolean;
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once, margin: "-80px" }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
