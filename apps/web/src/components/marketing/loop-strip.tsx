"use client";

import { Fragment } from "react";
import { ArrowRight, Link2, MousePointerClick, Copy } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";

const STEPS = [
  { icon: Link2, t: "Mỗi bản một short-link", d: "Tự gắn link đo riêng cho từng biến thể." },
  { icon: MousePointerClick, t: "Đếm click thật", d: "Người xem bấm thật, không phải view ảo." },
  { icon: Copy, t: "Clone bản thắng", d: "Nhân bản hook/giọng của bản bán được nhất." },
];

// Giải thích vòng lặp MOAT bằng 3 ô + mũi tên sáng dần.
export function LoopStrip() {
  return (
    <div className="mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-center">
      {STEPS.map((s, i) => (
        <Fragment key={s.t}>
          <Reveal delay={0.12 * i} className="flex-1 sm:max-w-[220px]">
            <div className="glass flex h-full flex-col gap-1.5 rounded-2xl p-4 text-left">
              <s.icon className="h-5 w-5 text-violet-300" />
              <div className="text-sm font-semibold text-ink-high">{`${i + 1}. ${s.t}`}</div>
              <div className="text-xs text-ink-low">{s.d}</div>
            </div>
          </Reveal>
          {i < STEPS.length - 1 && (
            <Reveal delay={0.12 * i + 0.08} className="grid shrink-0 place-items-center">
              <ArrowRight className="h-5 w-5 rotate-90 text-violet-400/70 sm:rotate-0" />
            </Reveal>
          )}
        </Fragment>
      ))}
    </div>
  );
}
