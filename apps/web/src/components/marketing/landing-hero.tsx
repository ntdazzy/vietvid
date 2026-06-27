"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Mic, Clock, Gift } from "lucide-react";
import { Button } from "@/components/ui/button";
import { DemoTile } from "@/components/marketing/demo-tile";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.06 * i, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

// Mẫu output THẬT của engine (public/samples/*.png). Khi render thật bật, thêm `video: "/samples/x.mp4"`
// vào từng mục là thẻ tự chuyển sang video tự chạy (DemoTile lo phần còn lại).
const DEMOS: { file: string; tag: string }[] = [
  { file: "fashion", tag: "Thời trang" },
  { file: "beauty", tag: "Mỹ phẩm" },
  { file: "tech", tag: "Công nghệ" },
  { file: "home", tag: "Gia dụng" },
  { file: "food", tag: "Ẩm thực" },
];

// so le nhẹ theo cột → "bức tường" editorial, không phải lưới thẻ đều nhau.
const OFFSET = ["sm:translate-y-6", "sm:-translate-y-2", "sm:translate-y-8", "", "sm:translate-y-4"];

export function LandingHero() {
  return (
    <section className="relative isolate overflow-hidden px-4 pb-20 pt-24">
      {/* glow tím sắc ở 1 điểm (không phải mesh tím-xanh) */}
      <div
        className="pointer-events-none absolute left-1/2 top-[-8%] h-[420px] w-[820px] -translate-x-1/2 opacity-60"
        style={{ background: "radial-gradient(50% 50% at 50% 50%, rgba(124,58,237,0.22), transparent 70%)" }}
      />

      <div className="mx-auto max-w-3xl text-center">
        <motion.span
          custom={0} variants={fadeUp} initial="hidden" animate="show"
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-[12px] font-medium text-ink-medium"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-success shadow-glow-success" />
          Engine giọng Việt thật · render trong ~60 giây
        </motion.span>

        <motion.h1
          custom={1} variants={fadeUp} initial="hidden" animate="show"
          className="font-display mx-auto mt-6 max-w-2xl text-[clamp(2.2rem,5.2vw,4rem)] font-bold leading-[1.02] tracking-[-0.035em] text-ink-high"
        >
          1 tấm ảnh sản phẩm.
          <br />
          <span className="text-gradient">Ra video chốt đơn.</span>
        </motion.h1>

        <motion.p
          custom={2} variants={fadeUp} initial="hidden" animate="show"
          className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-ink-medium"
        >
          KOL AI & video bán hàng giọng Việt tự nhiên — không cần máy quay, không cần ekip.
          Tải ảnh lên, chọn giọng, nhận video đăng được ngay.
        </motion.p>

        <motion.div
          custom={3} variants={fadeUp} initial="hidden" animate="show"
          className="mt-8 flex flex-wrap items-center justify-center gap-3"
        >
          <Link href="/login">
            <Button size="lg" className="gap-2">
              Tạo video đầu tiên <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <a href="#how">
            <Button variant="glass" size="lg">
              Cách hoạt động
            </Button>
          </a>
        </motion.div>

        {/* proof TRUNG THỰC — không bịa "50.000 creator" */}
        <motion.div
          custom={4} variants={fadeUp} initial="hidden" animate="show"
          className="mt-7 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-ink-low"
        >
          <span className="inline-flex items-center gap-1.5"><Clock className="h-4 w-4 text-violet-300" /> ~60 giây / video</span>
          <span className="inline-flex items-center gap-1.5"><Mic className="h-4 w-4 text-violet-300" /> Giọng Việt thật</span>
          <span className="inline-flex items-center gap-1.5"><Gift className="h-4 w-4 text-violet-300" /> Tặng 300 credit, không cần thẻ</span>
        </motion.div>
      </div>

      {/* demo wall: bức tường mẫu thật, thẻ tự chạy khi hover/lọt khung — KHÔNG nút play tròn */}
      <motion.div
        custom={5} variants={fadeUp} initial="hidden" animate="show"
        className="mx-auto mt-16 max-w-5xl"
      >
        <div className="mb-4 flex items-end justify-between px-1">
          <h2 className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-ink-low">
            Mẫu thật từ engine
          </h2>
          <Link href="/login" className="text-sm text-violet-300 transition hover:text-violet-200">
            Tự tạo thử →
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 sm:gap-4">
          {DEMOS.map((d, i) => (
            <DemoTile
              key={d.file}
              poster={`/samples/${d.file}.png`}
              label={d.tag}
              className={`aspect-[9/16] ${OFFSET[i]} ${i === 4 ? "hidden sm:block" : ""}`}
            />
          ))}
        </div>
      </motion.div>
    </section>
  );
}
