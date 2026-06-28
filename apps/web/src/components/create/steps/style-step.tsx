"use client";

import { Zap, Clapperboard, Gauge, Lock } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils/cn";
import { ScriptStudio } from "./script-studio";

const ENGINES = [
  { id: "seedance", name: "Seedance", note: "Rẻ, nhanh, hợp bản nháp", icon: Zap, available: true },
  { id: "veo", name: "Veo 3.1", note: "Chất lượng hero", icon: Clapperboard, available: false },
  { id: "kling", name: "Kling 3.0", note: "Điện ảnh", icon: Clapperboard, available: false },
  { id: "hailuo", name: "Hailuo", note: "Nhanh, rẻ", icon: Gauge, available: false },
];

// Hộp xem trước tỷ lệ (px) — gợi hình dáng khung mà không cần ảnh.
const ASPECTS = [
  { value: "9:16", label: "Dọc", box: { width: 18, height: 32 } },
  { value: "1:1", label: "Vuông", box: { width: 28, height: 28 } },
  { value: "16:9", label: "Ngang", box: { width: 32, height: 18 } },
];

export function StyleStep() {
  const w = useWizard();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">Phong cách & engine</h2>
        <p className="mt-1 text-sm text-ink-low">Chọn thời lượng, độ phân giải và engine tạo video.</p>
      </div>

      <Field label="Mục đích">
        <ChipGroup
          value={w.purpose}
          onChange={(v) => w.patch({ purpose: v })}
          options={[
            { value: "final", label: "Bản hoàn chỉnh" },
            { value: "draft", label: "Bản nháp (rẻ hơn)" },
          ]}
        />
      </Field>

      <Field label="Thời lượng">
        <ChipGroup
          value={w.seconds}
          onChange={(v) => w.patch({ seconds: v })}
          options={[5, 8, 10, 15].map((s) => ({ value: s, label: `${s}s` }))}
        />
      </Field>

      <Field label="Độ phân giải">
        <ChipGroup
          value={w.resolution}
          onChange={(v) => w.patch({ resolution: v })}
          options={[
            { value: "480p", label: "480p" },
            { value: "720p", label: "720p" },
            { value: "1080p", label: "1080p" },
          ]}
        />
      </Field>

      <Field label="Tỷ lệ khung hình" hint="Dọc cho TikTok/Reels, vuông cho feed, ngang cho YouTube.">
        <div className="grid grid-cols-3 gap-3">
          {ASPECTS.map((a) => {
            const active = w.aspect === a.value;
            return (
              <button
                key={a.value}
                type="button"
                onClick={() => w.patch({ aspect: a.value })}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-xl border p-3 transition-colors",
                  active ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                )}
              >
                <span
                  className={cn("rounded-sm border", active ? "border-violet-300 bg-violet-500/20" : "border-ink-low/50")}
                  style={a.box}
                />
                <span className={cn("text-xs font-medium", active ? "text-ink-high" : "text-ink-low")}>{a.value}</span>
                <span className="text-[10px] text-ink-low">{a.label}</span>
              </button>
            );
          })}
        </div>
      </Field>

      <div className="border-t border-white/[0.06] pt-6 font-display text-base font-semibold text-ink-high">
        Engine &amp; kịch bản
      </div>

      <Field label="Engine tạo video" hint="Veo/Kling/Hailuo sẽ mở ở bản M2.">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {ENGINES.map((e) => {
            const active = w.videoEngine === e.id;
            return (
              <button
                key={e.id}
                type="button"
                disabled={!e.available}
                onClick={() => e.available && w.patch({ videoEngine: e.id })}
                className={cn(
                  "relative flex flex-col items-start gap-1.5 rounded-xl border p-3 text-left transition-colors",
                  active
                    ? "border-violet-500/60 bg-violet-500/10 shadow-glow-sm"
                    : "border-white/10",
                  e.available ? "hover:border-white/20" : "opacity-50",
                )}
              >
                <e.icon className={cn("h-5 w-5", active ? "text-violet-300" : "text-ink-low")} />
                <span className="text-sm font-medium text-ink-high">{e.name}</span>
                <span className="text-[11px] leading-tight text-ink-low">{e.note}</span>
                {!e.available && (
                  <Badge tone="neutral" className="absolute right-2 top-2 gap-1 px-2 py-0.5">
                    <Lock className="h-2.5 w-2.5" /> M2
                  </Badge>
                )}
              </button>
            );
          })}
        </div>
      </Field>

      <Field label="Kịch bản & ý tưởng" hint="Tạo kịch bản bằng AI rồi sửa, hoặc tự viết brief bên dưới.">
        <ScriptStudio />
        <textarea
          className={cn(inputCls, "mt-3 min-h-[72px] resize-y")}
          value={w.brief}
          onChange={(e) => w.patch({ brief: e.target.value })}
          placeholder="Nhấn mạnh chống ồn + pin trâu, giọng trẻ trung."
        />
      </Field>
    </div>
  );
}
