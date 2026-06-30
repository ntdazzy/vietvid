"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";

// Một ảnh THẬT (fashion.png) ở 2 trạng thái CSS: trái xám = ảnh gốc, phải màu + Ken-Burns =
// khung video nói tiếng Việt. KHÔNG bịa ảnh thứ 2. Phụ đề minh hoạ tinh thần angle transformation.
const CAPTIONS = ["Trước nhìn chán lắm…", "Lên đời, tự tin hẳn!", "Soi gương mà mê!"];
// sticker nổi kiểu quảng cáo — nhún liên tục cho sống động.
const STICKERS = [
  { text: "🔥 Trend", className: "left-2.5 bottom-[88px] -rotate-6" },
  { text: "✨ Sang hẳn", className: "right-2.5 bottom-[104px] rotate-6" },
];

export function BeforeAfter({ src = "/samples/fashion.jpg" }: { src?: string }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [pos, setPos] = useState(50);
  const [cap, setCap] = useState(0);
  const dragging = useRef(false);
  const touched = useRef(false);

  // tự trượt qua lại LIÊN TỤC kiểu quảng cáo, dừng khi người dùng tự kéo.
  useEffect(() => {
    if (reduce || !inView) return;
    const seq = [50, 66, 80, 66, 50, 34, 20, 34];
    let i = 0;
    const id = setInterval(() => {
      if (touched.current) { clearInterval(id); return; }
      i = (i + 1) % seq.length;
      setPos(seq[i]);
    }, 850);
    return () => clearInterval(id);
  }, [inView, reduce]);

  // phụ đề chạy vòng (chỉ minh hoạ, không hứa sync mili-giây).
  useEffect(() => {
    if (reduce) return;
    const id = setInterval(() => setCap((c) => (c + 1) % CAPTIONS.length), 2200);
    return () => clearInterval(id);
  }, [reduce]);

  function move(clientX: number) {
    const el = ref.current;
    if (!el) return;
    touched.current = true;
    const r = el.getBoundingClientRect();
    setPos(Math.max(6, Math.min(94, ((clientX - r.left) / r.width) * 100)));
  }

  return (
    <div
      ref={ref}
      onPointerDown={(e) => { dragging.current = true; move(e.clientX); }}
      onPointerMove={(e) => dragging.current && move(e.clientX)}
      onPointerUp={() => (dragging.current = false)}
      onPointerLeave={() => (dragging.current = false)}
      className="relative aspect-[9/16] w-full max-w-[300px] cursor-ew-resize select-none overflow-hidden rounded-[20px] ring-1 ring-white/[0.08]"
    >
      {/* lớp dưới: ảnh gốc xám */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt="Ảnh gốc" className="absolute inset-0 h-full w-full object-cover brightness-75 grayscale" />

      {/* lớp trên: khung video màu, clip phần bên phải đường chia */}
      <div className="absolute inset-0" style={{ clipPath: `inset(0 0 0 ${pos}%)` }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt="Khung video"
          className="h-full w-full object-cover"
          style={reduce ? undefined : { animation: "vv-kenburns 9s ease-in-out infinite alternate" }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
      </div>

      {/* phụ đề Việt — nảy từng chữ kiểu caption quảng cáo, đặt ngoài lớp clip để luôn hiện đủ */}
      <div className="pointer-events-none absolute inset-x-0 bottom-4 z-10 flex flex-wrap justify-center gap-x-1.5 gap-y-1 px-3">
        {CAPTIONS[cap].split(" ").map((word, wi) => (
          <motion.span
            key={`${cap}-${wi}`}
            initial={reduce ? false : { opacity: 0, y: 12, scale: 0.6 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={reduce ? undefined : { delay: wi * 0.07, type: "spring", stiffness: 520, damping: 11 }}
            className="rounded-md bg-black/65 px-2 py-1 text-sm font-semibold text-white backdrop-blur-sm"
          >
            {word}
          </motion.span>
        ))}
      </div>

      {/* sticker nổi kiểu quảng cáo — nhún lên xuống liên tục */}
      {!reduce &&
        STICKERS.map((s, i) => (
          <motion.span
            key={s.text}
            animate={{ y: [0, -7, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.35 }}
            className={`pointer-events-none absolute z-10 rounded-full bg-violet-500/90 px-2.5 py-1 text-[11px] font-bold text-white shadow-lg backdrop-blur-sm ${s.className}`}
          >
            {s.text}
          </motion.span>
        ))}

      {/* nhãn 2 trạng thái */}
      <span className="absolute left-2.5 top-2.5 rounded-md bg-black/55 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white/80 backdrop-blur-sm">
        Ảnh gốc
      </span>
      <span className="absolute right-2.5 top-2.5 rounded-md bg-violet-500/30 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-100 backdrop-blur-sm">
        Khung video
      </span>

      {/* đường chia + tay cầm */}
      <div className="absolute inset-y-0 w-[2px] bg-white/80" style={{ left: `${pos}%` }}>
        <span className="absolute top-1/2 left-1/2 grid h-7 w-7 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-white/70 bg-black/50 text-[10px] text-white backdrop-blur-sm">
          ⇆
        </span>
      </div>
    </div>
  );
}
