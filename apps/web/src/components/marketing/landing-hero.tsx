"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Play, Sparkles, ArrowRight, Users } from "lucide-react";
import { Button } from "@/components/ui/button";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.07 * i, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

// showcase = ảnh AI THẬT do engine VietVid tạo (public/samples/*.png).
const SAMPLES = [
  { file: "fashion", tag: "Thời trang" },
  { file: "beauty", tag: "Mỹ phẩm" },
  { file: "tech", tag: "Công nghệ" },
  { file: "home", tag: "Gia dụng" },
  { file: "food", tag: "Ẩm thực" },
];

export function LandingHero() {
  return (
    <section className="relative isolate overflow-hidden px-4 pb-16 pt-24 text-center">
      <div className="glow-radial pointer-events-none absolute inset-x-0 -top-20 h-[460px]" />

      <div className="mx-auto max-w-4xl">
        <motion.span
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-3.5 py-1.5 text-[12px] font-medium text-violet-200"
        >
          <Sparkles className="h-3.5 w-3.5" /> Nền tảng video AI giọng Việt
        </motion.span>

        <motion.h1
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mx-auto mt-6 max-w-3xl text-[clamp(2rem,4.6vw,3.5rem)] font-extrabold leading-[1.08] tracking-[-0.03em] text-ink-high"
        >
          KOL AI & video bán hàng,
          <br />
          <span className="text-gradient">chỉ từ 1 tấm ảnh.</span>
        </motion.h1>

        <motion.p
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-ink-medium"
        >
          Giọng Việt thật, video chốt đơn trong 60 giây. Không cần máy quay, không cần ekip.
        </motion.p>

        <motion.div
          custom={3}
          variants={fadeUp}
          initial="hidden"
          animate="show"
          className="mt-8 flex flex-wrap items-center justify-center gap-3"
        >
          <Link href="/login">
            <Button size="lg" className="gap-2">
              Tạo video ngay <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <a href="#how">
            <Button variant="glass" size="lg" className="gap-2">
              <Play className="h-4 w-4 text-violet-300" /> Xem demo 60 giây
            </Button>
          </a>
        </motion.div>
      </div>

      {/* sample showcase grid (autovis: lưới gương mặt creator) */}
      <motion.div
        custom={4}
        variants={fadeUp}
        initial="hidden"
        animate="show"
        className="mx-auto mt-14 max-w-4xl"
      >
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
          {SAMPLES.map((s, i) => (
            <div
              key={s.file}
              className={`glass-bordered group relative aspect-[9/16] overflow-hidden ${
                i >= 3 ? "hidden sm:block" : ""
              }`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/samples/${s.file}.png`}
                alt={s.tag}
                className="h-full w-full object-cover opacity-90 transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-bg-base/85 via-transparent to-transparent" />
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between p-2.5">
                <span className="rounded-full bg-bg-base/60 px-2 py-0.5 text-[10px] text-ink-medium backdrop-blur-sm">
                  {s.tag}
                </span>
                <span className="grid h-7 w-7 place-items-center rounded-full bg-violet-500/80 backdrop-blur-sm">
                  <Play className="h-3 w-3 translate-x-0.5 text-white" />
                </span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-ink-medium">
          <Users className="h-4 w-4 text-violet-300" />
          Tặng <span className="font-numeric font-semibold text-ink-high">300</span> credit cho người mới · không cần thẻ
        </div>
      </motion.div>
    </section>
  );
}
