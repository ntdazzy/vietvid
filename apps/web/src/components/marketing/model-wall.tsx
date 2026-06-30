import { Reveal } from "@/components/marketing/reveal";

// Moat "tổng hợp nhiều model": show thẳng các engine thay vì chỉ nói trong microcopy.
// Trạng thái thật — đang dùng vs sắp có (không khoe model chưa tích hợp như đã có).
const MODELS = [
  { name: "Seedance 2.0", use: "Video", live: true },
  { name: "Gemini · Imagen", use: "Ảnh", live: true },
  { name: "Nhân vật AI", use: "KOL nhất quán", live: true },
  { name: "Giọng Việt", use: "7 giọng TTS", live: true },
  { name: "Kling", use: "Video", live: false },
  { name: "Grok Imagine", use: "Ảnh/Video", live: false },
];

export function ModelWall() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-10">
      <Reveal>
        <div className="rounded-3xl glass-bordered px-5 py-6 sm:px-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:gap-8">
            <div className="lg:w-64 lg:shrink-0">
              <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-300">Tổng hợp nhiều model AI</div>
              <p className="mt-1.5 text-sm text-ink-medium">Chọn đúng model cho từng việc — không khóa cứng một engine.</p>
            </div>
            <div className="flex flex-1 flex-wrap gap-2.5">
              {MODELS.map((m) => (
                <div
                  key={m.name}
                  className="flex items-center gap-2.5 rounded-xl border border-white/[0.08] bg-white/[0.025] px-3.5 py-2.5"
                >
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-violet-500/15 font-display text-xs font-bold text-violet-200">
                    {m.name.charAt(0)}
                  </span>
                  <div className="leading-tight">
                    <div className="text-sm font-semibold text-ink-high">{m.name}</div>
                    <div className="text-[11px] text-ink-low">{m.use}</div>
                  </div>
                  <span
                    className={
                      "ml-1 shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-medium " +
                      (m.live ? "bg-success/15 text-success" : "bg-white/[0.06] text-ink-low")
                    }
                  >
                    {m.live ? "đang dùng" : "sắp có"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
