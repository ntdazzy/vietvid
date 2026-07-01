"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils/cn";

/** Nút "lên đầu trang" — hiện khi cuộn quá 1 màn, bấm cuộn mượt về đầu.
 *  Thiết kế premium: kính mờ + viền/glow tím + xuất hiện/ẩn mượt, tôn trọng reduced-motion. */
export function ScrollToTop() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 640);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <button
      type="button"
      aria-label="Lên đầu trang"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      className={cn(
        "group fixed bottom-6 right-6 z-40 grid h-12 w-12 place-items-center rounded-full",
        "border border-violet-400/30 bg-bg-elevated/70 text-violet-200 backdrop-blur-xl",
        "shadow-[0_10px_34px_-8px_rgba(124,77,255,0.55)]",
        "transition-all duration-300 hover:-translate-y-0.5 hover:border-violet-400/60 hover:bg-violet-500/20 hover:text-white",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50",
        show ? "translate-y-0 opacity-100" : "pointer-events-none translate-y-3 opacity-0",
      )}
    >
      {/* vòng glow mảnh khi hover */}
      <span className="pointer-events-none absolute inset-0 rounded-full opacity-0 ring-1 ring-violet-400/40 transition-opacity duration-300 group-hover:opacity-100" />
      <ArrowUp className="h-5 w-5 transition-transform duration-300 group-hover:-translate-y-0.5" />
    </button>
  );
}
