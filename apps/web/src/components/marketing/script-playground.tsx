"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Sparkles, Pencil } from "lucide-react";

// MOCK client-side (endpoint /v1/script/* cần auth → không gọi được trên landing public).
// Data dùng đúng giọng + nhãn góc/beat THẬT của engine (scriptgen.py).
type Beat = { t: string; label: string; text: string };
type Preset = { label: string; product: string; angle: string; hook: string; beats: Beat[] };

const PRESETS: Preset[] = [
  {
    label: "Serum dưỡng trắng", product: "Serum dưỡng trắng", angle: "Lột xác trước → sau",
    hook: "Da xỉn 7 ngày trước với giờ — khác một trời một vực!",
    beats: [
      { t: "00:00", label: "Hook", text: "Trước với sau khi dùng serum này, nhìn là biết liền." },
      { t: "00:05", label: "Nỗi đau", text: "Hồi đó da mình xỉn, lỗ chân lông to, ngại soi gương." },
      { t: "00:12", label: "Lợi ích", text: "Dùng đều mỗi tối là da sáng mịn, tự tin hẳn ra." },
      { t: "00:20", label: "Chốt", text: "Để link giỏ hàng rồi nha, bấm thử cho biết!" },
    ],
  },
  {
    label: "Tai nghe bluetooth", product: "Tai nghe bluetooth", angle: "So sánh hơn hẳn",
    hook: "Thử tai nghe này xong là khỏi quay lại loại cũ luôn!",
    beats: [
      { t: "00:00", label: "Hook", text: "Đặt cạnh tai nghe cũ là thấy khác liền." },
      { t: "00:05", label: "Nỗi đau", text: "Loại rẻ tiền nghe rè, rớt kết nối hoài, bực ghê." },
      { t: "00:12", label: "Lợi ích", text: "Cái này pin trâu, chống ồn, đáng từng đồng." },
      { t: "00:20", label: "Chốt", text: "Có nhiêu mà nâng cấp hẳn, bấm giỏ hàng đi nha!" },
    ],
  },
  {
    label: "Nồi chiên không dầu", product: "Nồi chiên không dầu", angle: "Sợ bỏ lỡ / sắp hết",
    hook: "Nồi chiên đang sale sốc, hết hàng là tiếc lắm nha!",
    beats: [
      { t: "00:00", label: "Hook", text: "Canh mãi mới thấy đợt giảm sâu vầy nè." },
      { t: "00:06", label: "Lợi ích", text: "Đợt này giá hời, qua đợt là về giá gốc liền." },
      { t: "00:13", label: "Khao khát", text: "Mua về nấu gì cũng nhanh, cả nhà mê tít." },
      { t: "00:21", label: "Chốt", text: "Còn hàng là còn cơ hội, chốt liền tay nha!" },
    ],
  },
  {
    label: "Áo khoác dù", product: "Áo khoác dù", angle: "Đám đông tin dùng",
    hook: "Cả nhà rủ nhau mua áo này, mình cũng phải thử!",
    beats: [
      { t: "00:00", label: "Hook", text: "Lướt đâu cũng thấy người ta khoe áo này." },
      { t: "00:06", label: "Lợi ích", text: "Mặc lên nhẹ, ấm, đi mưa đi nắng đều hợp." },
      { t: "00:13", label: "Khao khát", text: "Giờ tới lượt mình nghiện, mua là không hối." },
      { t: "00:21", label: "Chốt", text: "Còn chần chừ gì, chốt cùng hội luôn nè!" },
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
      hook: `${q} — thử là mê, chốt đơn liền tay!` });
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
          placeholder="Tên sản phẩm của bạn…"
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
          Góc: <span className="text-violet-300">{active.angle}</span>
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
