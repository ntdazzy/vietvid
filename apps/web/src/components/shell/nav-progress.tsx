"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

/**
 * Thanh tiến trình mảnh trên đỉnh khi ĐIỀU HƯỚNG — cảm giác "đang dựng/đang tải" như studio.
 * Bắt click vào link nội bộ → bò tới ~90%; khi pathname đổi (đã sang trang) → chạy nốt 100% rồi ẩn.
 * Thuần opacity/width nên an toàn với prefers-reduced-motion (không phải animation lặp).
 */
export function NavProgress() {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);
  const [width, setWidth] = useState(0);
  const creep = useRef<ReturnType<typeof setInterval> | null>(null);
  const active = useRef(false);

  function stopCreep() {
    if (creep.current) { clearInterval(creep.current); creep.current = null; }
  }

  function start() {
    active.current = true;
    setVisible(true);
    setWidth(10);
    stopCreep();
    creep.current = setInterval(() => {
      setWidth((w) => (w < 90 ? w + (90 - w) * 0.12 : w));
    }, 220);
  }

  // Bắt đầu khi click link nội bộ (Link render ra <a>).
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = (e.target as HTMLElement)?.closest?.("a");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href || !href.startsWith("/")) return; // chỉ điều hướng nội bộ
      if (a.getAttribute("target") === "_blank") return;
      if (href === window.location.pathname + window.location.search) return; // cùng trang
      start();
    }
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  // Hoàn tất khi pathname đổi (trang mới đã commit).
  useEffect(() => {
    if (!active.current) return;
    stopCreep();
    setWidth(100);
    const t = setTimeout(() => { active.current = false; setVisible(false); setWidth(0); }, 350);
    return () => clearTimeout(t);
  }, [pathname]);

  return (
    <div aria-hidden className="pointer-events-none fixed inset-x-0 top-0 z-[200] h-[3px]">
      <div
        className="h-full rounded-r-full bg-gradient-to-r from-violet-500 via-indigo-400 to-fuchsia-400 shadow-[0_0_12px_rgba(124,77,255,0.7)] transition-[width,opacity] duration-300 ease-out"
        style={{ width: `${width}%`, opacity: visible ? 1 : 0 }}
      />
    </div>
  );
}
