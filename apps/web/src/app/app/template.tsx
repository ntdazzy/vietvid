"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * Chuyển cảnh giữa các màn /app — "cut phim" (fade + trượt nhẹ). template.tsx re-mount
 * mỗi lần điều hướng nên animation enter chạy lại → cảm giác chuyển màn mượt.
 * Tôn trọng prefers-reduced-motion (tắt hẳn animation).
 */
export default function AppTemplate({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduce ? 0 : 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
