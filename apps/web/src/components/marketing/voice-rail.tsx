"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

// Data THẬT từ app_api/voices.py (7 persona). KHÔNG phát audio giả: chưa có mp3 + endpoint cần
// auth → waveform TĨNH (chỉ "thở" khi hover), nghe thử thật ở trong app.
type Voice = { name: string; vibe: string; gender: "f" | "m" };
const VOICES: Voice[] = [
  { name: "Mai", vibe: "Trẻ trung, năng động", gender: "f" },
  { name: "Linh", vibe: "Nhẹ nhàng, tâm tình", gender: "f" },
  { name: "Trang", vibe: "Rõ ràng, chuyên nghiệp", gender: "f" },
  { name: "Bống", vibe: "Láu lỉnh, dí dỏm", gender: "f" },
  { name: "Khoa", vibe: "Năng động, cuốn hút", gender: "m" },
  { name: "Hùng", vibe: "Trầm ấm, tin cậy", gender: "m" },
  { name: "Tú", vibe: "Trẻ trung, vui vẻ", gender: "m" },
];

// chiều cao cột sóng (tĩnh) — gợi hình giọng, không phải phổ audio thật.
const BARS = [0.4, 0.7, 0.45, 0.9, 0.6, 1, 0.5, 0.8, 0.45, 0.7, 0.55, 0.85];

function Wave() {
  return (
    <div className="flex h-7 items-center gap-[3px]">
      {BARS.map((h, i) => (
        <span
          key={i}
          className="w-[3px] origin-center rounded-full bg-violet-400/60 transition-transform group-hover:[animation:vv-wave_0.9s_ease-in-out_infinite]"
          style={{ height: `${h * 100}%`, animationDelay: `${i * 60}ms` }}
        />
      ))}
    </div>
  );
}

export function VoiceRail() {
  return (
    <div className="flex flex-wrap justify-center gap-3 lg:flex-nowrap lg:justify-start lg:overflow-x-auto lg:pb-2">
      {VOICES.map((v, i) => (
        <Reveal key={v.name} delay={0.06 * i} className={cn("shrink-0", i % 2 === 1 && "lg:translate-y-4")}>
          <div className="group glass w-[220px] rounded-2xl p-4">
            <div className="flex items-center gap-3">
              <span
                className={cn(
                  "grid h-10 w-10 shrink-0 place-items-center rounded-full text-sm font-bold",
                  v.gender === "f" ? "bg-rose-500/15 text-rose-200" : "bg-sky-500/15 text-sky-200",
                )}
              >
                {v.name.charAt(0)}
              </span>
              <div className="min-w-0">
                <div className="text-sm font-semibold text-ink-high">{v.name}</div>
                <div className="truncate text-xs text-ink-low">{v.vibe}</div>
              </div>
            </div>
            <div className="mt-3">
              <Wave />
            </div>
            <Link
              href="/login"
              className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-violet-300 transition hover:text-violet-200"
            >
              Nghe thử trong app <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </Reveal>
      ))}
    </div>
  );
}
