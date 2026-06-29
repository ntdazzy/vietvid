"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { useTranslations } from "next-intl";
import { VyraMark } from "@/components/brand/logo";

// Intro điện ảnh: logo Vyra vẽ ra → wordmark + tagline → mở vào trang.
// LUÔN hiện mỗi lần vào trang, tự tắt sau ~1.8s (không có nút bỏ qua).
// Vẫn cho click/cuộn để tắt sớm; reduced-motion → hiện logo tĩnh, tắt nhanh hơn.
export function Intro() {
  const t = useTranslations("home");
  const reduce = useReducedMotion();
  // show=true ngay từ SSR → overlay phủ trang TỪ ĐẦU, không lộ hero 1 nhịp rồi mới ra intro.
  const [show, setShow] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setShow(false), reduce ? 1300 : 1800);
    const skip = (e: Event) => {
      if (e.type === "keydown" && (e as KeyboardEvent).key !== "Escape") return;
      setShow(false);
    };
    window.addEventListener("keydown", skip);
    window.addEventListener("wheel", skip, { passive: true });
    return () => {
      clearTimeout(t);
      window.removeEventListener("keydown", skip);
      window.removeEventListener("wheel", skip);
    };
  }, [reduce]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="vyra-intro"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.04 }}
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
            <VyraMark animated={!reduce} className="h-24 w-24 drop-shadow-[0_0_28px_rgba(124,77,255,0.5)]" />
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : 1.0, duration: 0.5 }}
              className="mt-5 text-center"
            >
              {/* wordmark + vệt sáng quét qua */}
              <div className="relative inline-block overflow-hidden">
                <span className="font-display text-3xl font-extrabold tracking-tight text-ink-high">Vyra</span>
                {!reduce && (
                  <motion.span
                    aria-hidden
                    initial={{ x: "-120%" }}
                    animate={{ x: "120%" }}
                    transition={{ delay: 0.9, duration: 0.7, ease: "easeInOut" }}
                    className="absolute inset-y-0 left-0 w-1/3 -skew-x-12 bg-white/20 mix-blend-overlay"
                  />
                )}
              </div>
              <div className="mt-1 text-sm tracking-wide text-ink-low">{t("introTagline")}</div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
