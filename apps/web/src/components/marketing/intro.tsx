"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { VyraMark } from "@/components/brand/logo";

const KEY = "vyra_intro_seen";

// Intro điện ảnh khi vào web: logo Vyra tự vẽ ra → wordmark + tagline fade → mở vào trang.
// Chỉ 1 lần/phiên (sessionStorage), bỏ được (skip/click), tôn trọng reduced-motion.
export function Intro() {
  const reduce = useReducedMotion();
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (reduce) return; // giảm chuyển động → bỏ intro
    try {
      if (sessionStorage.getItem(KEY)) return;
      sessionStorage.setItem(KEY, "1");
    } catch {
      /* private mode → vẫn cho chạy 1 lần */
    }
    setShow(true);
    const t = setTimeout(() => setShow(false), 2600);
    return () => clearTimeout(t);
  }, [reduce]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="vyra-intro"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          onClick={() => setShow(false)}
          className="fixed inset-0 z-[100] grid cursor-pointer place-items-center bg-[#06070d]"
        >
          {/* vầng tím nền */}
          <div
            className="pointer-events-none absolute inset-0 opacity-70"
            style={{ background: "radial-gradient(40% 40% at 50% 45%, rgba(124,77,255,0.18), transparent 70%)" }}
          />
          <div className="relative flex flex-col items-center">
            <VyraMark animated className="h-24 w-24 drop-shadow-[0_0_28px_rgba(124,77,255,0.5)]" />
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.15, duration: 0.5 }}
              className="mt-5 text-center"
            >
              <div className="font-display text-3xl font-extrabold tracking-tight text-ink-high">Vyra</div>
              <div className="mt-1 text-sm tracking-wide text-ink-low">Video viral ra đơn · giọng Việt thật</div>
            </motion.div>
          </div>

          <motion.button
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.6 }}
            onClick={(e) => { e.stopPropagation(); setShow(false); }}
            className="absolute bottom-8 text-xs text-ink-low transition hover:text-ink-medium"
          >
            Bỏ qua →
          </motion.button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
