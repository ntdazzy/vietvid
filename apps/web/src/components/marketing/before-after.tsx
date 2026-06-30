"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";

// Trái = ẢNH GỐC tĩnh (xám, KHÔNG chữ). Phải = KHUNG VIDEO thật (mp4 chạy) + phụ đề Việt.
// Gạt thanh trượt để lộ video bên phải — đúng tinh thần "ảnh đứng yên → AI cho chuyển động".
const CAPTIONS = ["Trước nhìn chán lắm…", "Có rồi là lên đời, tự tin hẳn.", "Soi gương mà mê!"];

export function BeforeAfter({
  src = "/showcase/gaixinh.jpg",
  video = "/showcase/gaixinh.mp4",
}: {
  src?: string;
  video?: string;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const vref = useRef<HTMLVideoElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const [pos, setPos] = useState(50);
  const [cap, setCap] = useState(0);
  const [manual, setManual] = useState(false); // người dùng đã tự kéo → tắt hiệu ứng tự trượt
  const dragging = useRef(false);
  const touched = useRef(false);

  // tự trượt mượt: dịch giữa các mốc bằng CSS transition (không nhảy cứng → hết giật).
  const glide = !manual && !reduce ? "clip-path 820ms cubic-bezier(0.4,0,0.2,1), left 820ms cubic-bezier(0.4,0,0.2,1)" : "none";

  // video bên phải tự chạy khi lọt khung.
  useEffect(() => {
    const v = vref.current;
    if (!v || !inView) return;
    v.play().catch(() => {});
  }, [inView]);

  // tự trượt qua lại để khoe before→after, dừng ngay khi người dùng tự kéo.
  useEffect(() => {
    if (reduce || !inView) return;
    const seq = [50, 66, 80, 66, 50, 34, 20, 34];
    let i = 0;
    const id = setInterval(() => {
      if (touched.current) { clearInterval(id); return; }
      i = (i + 1) % seq.length;
      setPos(seq[i]);
    }, 900);
    return () => clearInterval(id);
  }, [inView, reduce]);

  // phụ đề Việt chạy vòng (chỉ minh hoạ, không hứa sync mili-giây).
  useEffect(() => {
    if (reduce) return;
    const id = setInterval(() => setCap((c) => (c + 1) % CAPTIONS.length), 2400);
    return () => clearInterval(id);
  }, [reduce]);

  function move(clientX: number) {
    const el = ref.current;
    if (!el) return;
    touched.current = true;
    setManual(true); // chuyển sang kéo tay → bỏ transition để bám con trỏ tức thì
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
      {/* lớp dưới: ẢNH GỐC xám tĩnh — KHÔNG chữ, không gì hết */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt="Ảnh gốc" className="absolute inset-0 h-full w-full object-cover brightness-75 grayscale" />

      {/* lớp trên: KHUNG VIDEO THẬT (mp4 chạy), clip phần bên phải đường chia. Chữ CHỈ ở đây. */}
      <div className="absolute inset-0" style={{ clipPath: `inset(0 0 0 ${pos}%)`, transition: glide, willChange: "clip-path" }}>
        <video
          ref={vref}
          src={video}
          poster={src}
          muted
          loop
          playsInline
          preload="metadata"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
        {/* phụ đề Việt — 1 dòng, kiểu sang (như cũ) */}
        <div className="absolute inset-x-0 bottom-4 flex justify-center px-3">
          <motion.span
            key={cap}
            initial={reduce ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-md bg-black/55 px-2.5 py-1 text-center text-sm font-semibold text-white backdrop-blur-sm"
          >
            {CAPTIONS[cap]}
          </motion.span>
        </div>
      </div>

      {/* nhãn 2 trạng thái */}
      <span className="absolute left-2.5 top-2.5 rounded-md bg-black/55 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white/80 backdrop-blur-sm">
        Ảnh gốc
      </span>
      <span className="absolute right-2.5 top-2.5 rounded-md bg-violet-500/30 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-100 backdrop-blur-sm">
        Khung video
      </span>

      {/* đường chia + tay cầm */}
      <div className="absolute inset-y-0 w-[2px] bg-white/80" style={{ left: `${pos}%`, transition: glide, willChange: "left" }}>
        <span className="absolute top-1/2 left-1/2 grid h-7 w-7 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-white/70 bg-black/50 text-[10px] text-white backdrop-blur-sm">
          ⇆
        </span>
      </div>
    </div>
  );
}
