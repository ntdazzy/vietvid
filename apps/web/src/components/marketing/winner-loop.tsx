"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion, animate } from "framer-motion";
import { TrendingUp, Copy, Trophy } from "lucide-react";
import { cn } from "@/lib/utils/cn";

// MOCK minh hoạ — KHÔNG phải dữ liệu khách hàng. Vòng lặp THẬT có trong backend (series.py):
// job → short-link/biến thể → đếm click → xếp hạng → nhân bản bản thắng.
type Variant = { tag: string; angle: string; link: string; ctr: number; clicks: number; sample: string };

const VARIANTS: Variant[] = [
  { tag: "Biến thể A", angle: "So sánh hơn hẳn", link: "vv.id/a3f", ctr: 92, clicks: 1840, sample: "tech" },
  { tag: "Biến thể B", angle: "Sợ bỏ lỡ / sắp hết", link: "vv.id/b7k", ctr: 74, clicks: 1310, sample: "beauty" },
  { tag: "Biến thể C", angle: "Đám đông tin dùng", link: "vv.id/c2m", ctr: 58, clicks: 980, sample: "fashion" },
  { tag: "Biến thể D", angle: "Lột xác trước → sau", link: "vv.id/d9p", ctr: 41, clicks: 620, sample: "food" },
];

function CountUp({ to }: { to: number }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [val, setVal] = useState(reduce ? to : 0);
  useEffect(() => {
    if (reduce || !inView) return;
    const controls = animate(0, to, {
      duration: 1.1, ease: [0.22, 1, 0.36, 1], onUpdate: (v) => setVal(Math.round(v)),
    });
    return () => controls.stop();
  }, [inView, to, reduce]);
  return <span ref={ref} className="font-numeric tabular">{val.toLocaleString("vi-VN")}</span>;
}

export function VariantLeaderboard() {
  const reduce = useReducedMotion();
  return (
    <div className="glass-bordered mx-auto max-w-2xl rounded-[24px] p-4 sm:p-5">
      <div className="mb-3 flex items-center justify-between px-1 text-xs text-ink-low">
        <span className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider">
          <TrendingUp className="h-3.5 w-3.5 text-violet-300" /> Bảng xếp hạng theo click thật
        </span>
        <span>4 biến thể · 1 sản phẩm</span>
      </div>
      <div className="flex flex-col gap-2">
        {VARIANTS.map((v, i) => {
          const winner = i === 0;
          return (
            <motion.div
              key={v.tag}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: reduce ? 0 : 0.1 * i, duration: 0.45 }}
              className={cn(
                "flex items-center gap-3 rounded-2xl border p-2.5",
                winner ? "border-success/50 bg-success/[0.05]" : "border-white/[0.06] bg-white/[0.02]",
              )}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`/samples/${v.sample}.jpg`} alt="" className="h-12 w-9 shrink-0 rounded-lg object-cover" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-semibold text-ink-high">{v.tag}</span>
                  <span className="truncate text-[11px] text-ink-low">· {v.angle}</span>
                  {winner && (
                    <motion.span
                      initial={{ scale: 0.7, opacity: 0 }}
                      whileInView={{ scale: 1, opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{ delay: reduce ? 0 : 0.5, type: "spring", stiffness: 200 }}
                      className="ml-auto inline-flex shrink-0 items-center gap-1 rounded-md bg-success/15 px-1.5 py-0.5 text-[10px] font-bold text-success"
                    >
                      <Trophy className="h-3 w-3" /> Bản thắng
                    </motion.span>
                  )}
                </div>
                {/* thanh CTR */}
                <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div
                    className={cn("h-full rounded-full", winner ? "bg-success" : "bg-grad-brand")}
                    initial={{ width: 0 }}
                    whileInView={{ width: `${v.ctr}%` }}
                    viewport={{ once: true, margin: "-40px" }}
                    transition={{ delay: reduce ? 0 : 0.15 + 0.1 * i, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                  />
                </div>
                <div className="mt-1 flex items-center gap-3 text-[11px] text-ink-low">
                  <span className="font-numeric text-violet-300">{v.link}</span>
                  <span><CountUp to={v.clicks} /> click</span>
                </div>
              </div>
              {winner && (
                <span className="hidden shrink-0 items-center gap-1 rounded-lg border border-success/40 px-2 py-1 text-[11px] font-medium text-success sm:inline-flex">
                  <Copy className="h-3 w-3" /> Nhân bản
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
      <p className="mt-3 text-center text-xs text-ink-low">
        Số liệu minh hoạ cách hệ thống xếp hạng — không phải dữ liệu khách hàng.
      </p>
    </div>
  );
}
