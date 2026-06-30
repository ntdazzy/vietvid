"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Sparkles, Pencil } from "lucide-react";

// MOCK client-side (endpoint thật cần auth → không gọi được trên landing public).
// Demo ĐA-MODEL: một ý tưởng → Vyra chọn model AI hợp việc → preview output (video/ảnh/nhân vật/giọng).
type Beat = { t: string; label: string; text: string };
type Preset = { label: string; product: string; model: string; kind: string; hook: string; beats: Beat[] };

const PRESETS: Preset[] = [
  {
    label: "Video review", product: "Video review serum", model: "Seedance 2.0", kind: "Video",
    hook: "Da xỉn 7 ngày trước với giờ — khác một trời một vực!",
    beats: [
      { t: "Hook", label: "Mở", text: "Trước với sau khi dùng serum này, nhìn là biết liền." },
      { t: "Kịch bản", label: "AI viết", text: "Hook → nỗi đau → lợi ích → chốt, theo timecode." },
      { t: "Giọng", label: "Lồng tiếng", text: "Chọn 1 trong 7 giọng Việt thật, phụ đề khớp khung." },
      { t: "Xuất", label: "Output", text: "Video 60s, đủ 3 tỉ lệ — dọc, vuông, ngang." },
    ],
  },
  {
    label: "Ảnh sản phẩm", product: "Ảnh serum nền pastel", model: "Gemini · Imagen", kind: "Ảnh",
    hook: "Ảnh studio, ánh sáng mềm, nền pastel — sắc nét, bám mô tả.",
    beats: [
      { t: "Mô tả", label: "Prompt", text: "Gõ một câu, AI hiểu phong cách bạn muốn." },
      { t: "Style", label: "Phong cách", text: "Editorial, tông pastel hồng, nền sạch." },
      { t: "Model", label: "Engine", text: "Gemini/Imagen — chữ trong ảnh chuẩn, độ nét cao." },
      { t: "Xuất", label: "Output", text: "Ảnh tải về ngay, dọc 9:16 hoặc vuông 1:1." },
    ],
  },
  {
    label: "Nhân vật AI", product: "KOL nữ trẻ trung", model: "Nhân vật AI", kind: "Nhân vật",
    hook: "Diễn viên AI nhất quán — giữ gương mặt qua mọi video.",
    beats: [
      { t: "Tạo", label: "Khởi tạo", text: "Từ ảnh, mô tả, hoặc tự dựng thuộc tính." },
      { t: "Vibe", label: "Phong cách", text: "Trẻ trung, thân thiện, giọng nữ Việt." },
      { t: "Dùng", label: "Tái dùng", text: "Đưa vào ảnh & video sau này." },
      { t: "Khóa", label: "Nhất quán", text: "Giữ gương mặt mỗi lần sinh lại." },
    ],
  },
  {
    label: "Giọng đọc", product: "Lồng giọng quảng cáo", model: "Giọng Việt", kind: "Giọng",
    hook: "7 giọng Việt thật — chọn giọng hợp ngành, nghe thử ngay.",
    beats: [
      { t: "Chọn", label: "Giọng", text: "Mai, Linh, Khoa… 7 cá tính khác nhau." },
      { t: "Nhập", label: "Lời thoại", text: "Dán kịch bản, AI đọc tự nhiên như người." },
      { t: "Nghe", label: "Preview", text: "Nghe thử ngay trước khi dùng." },
      { t: "Ghép", label: "Lồng video", text: "Khớp phụ đề theo timecode." },
    ],
  },
];

export function ScriptPlayground() {
  const reduce = useReducedMotion();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState<Preset>(PRESETS[0]);
  const [typed, setTyped] = useState(reduce ? PRESETS[0].hook : "");
  const [done, setDone] = useState(reduce);
  // chưa "kick" thì vùng kết quả chờ — tránh gõ-trên-mount rồi 1.2s lại gõ lại.
  const [kicked, setKicked] = useState(reduce);

  // auto-demo: 1.2s sau mount mới bắt đầu gõ preset đầu (chỉ 1 lần).
  useEffect(() => {
    if (reduce || kicked) return;
    const id = setTimeout(() => setKicked(true), 1200);
    return () => clearTimeout(id);
  }, [reduce, kicked]);

  // typewriter hook: chỉ chạy sau khi đã kick; reduced-motion → hiện full ngay.
  useEffect(() => {
    if (!kicked) return;
    if (reduce) {
      setTyped(active.hook);
      setDone(true);
      return;
    }
    setTyped("");
    setDone(false);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setTyped(active.hook.slice(0, i));
      if (i >= active.hook.length) {
        clearInterval(id);
        setDone(true);
      }
    }, 28);
    return () => clearInterval(id);
  }, [active, kicked, reduce]);

  function run(p: Preset) {
    setKicked(true);
    setQuery(p.product);
    setActive(p);
  }
  function submit() {
    const q = query.trim();
    if (!q) return;
    setKicked(true);
    // gắn sản phẩm người dùng gõ vào khung kết quả của 1 góc mặc định.
    setActive({ ...PRESETS[0], product: q, label: q,
      hook: `${q} — Vyra chọn model AI hợp nhất để dựng.` });
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.25, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="glass-bordered rounded-[24px] p-5"
    >
      {/* nhập + preset */}
      <div className="flex items-center gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Mô tả ý tưởng của bạn…"
          className="w-full rounded-xl border border-white/10 bg-bg-base/50 px-3.5 py-2.5 text-sm text-ink-high outline-none placeholder:text-ink-low focus:border-violet-500/40"
        />
        <button
          onClick={submit}
          className="shrink-0 rounded-xl bg-grad-brand px-3.5 py-2.5 text-sm font-semibold text-white shadow-glow-sm transition active:scale-95"
        >
          Viết
        </button>
      </div>
      <div className="mt-2.5 flex flex-wrap gap-1.5">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => run(p)}
            className={
              "rounded-lg border px-2.5 py-1 text-xs transition-colors " +
              (active.label === p.label
                ? "border-violet-500/60 bg-violet-500/15 text-violet-100"
                : "border-white/10 text-ink-low hover:border-white/25")
            }
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* kết quả */}
      <div className="mt-4 rounded-2xl border border-white/[0.06] bg-bg-base/40 p-4">
        <div className="text-[11px] uppercase tracking-wider text-ink-low">
          Model: <span className="text-violet-300">{active.model}</span> · {active.kind}
        </div>
        <p className="mt-2 min-h-[2.4em] font-display text-lg font-bold leading-snug text-gradient">
          {typed}
          {!done && <span className="caret-blink text-violet-300">▍</span>}
        </p>

        <AnimatePresence>
          {done && (
            <motion.ul className="mt-3 flex flex-col gap-1.5">
              {active.beats.map((b, i) => (
                <motion.li
                  key={b.t + b.text}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: reduce ? 0 : 0.12 * i, duration: 0.4 }}
                  className="flex gap-2.5 text-sm"
                >
                  <span className="shrink-0 font-numeric text-[11px] text-ink-low">{b.t}</span>
                  <span className="shrink-0 text-[11px] font-semibold uppercase tracking-wide text-violet-300/80">
                    {b.label}
                  </span>
                  <span className="text-ink-medium">{b.text}</span>
                </motion.li>
              ))}
            </motion.ul>
          )}
        </AnimatePresence>

        <div className="mt-3 flex items-center gap-1.5 text-[11px] text-ink-low">
          <Pencil className="h-3 w-3" /> Sửa được từng dòng trong app
          <Sparkles className="ml-auto h-3 w-3 text-violet-300" /> Mô phỏng — bản đầy đủ trong app
        </div>
      </div>
    </motion.div>
  );
}
