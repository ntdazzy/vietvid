"use client";

import Link from "next/link";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import { ArrowRight, Mic, Clock, Gift } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScriptPlayground } from "@/components/marketing/script-playground";

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.06 * i, duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  }),
};

export function LandingHero() {
  const reduce = useReducedMotion();
  const { scrollY } = useScroll();
  const glowYRaw = useTransform(scrollY, [0, 500], [0, -80]);
  const glowY = reduce ? 0 : glowYRaw;

  return (
    <section className="relative isolate overflow-hidden pt-28 pb-20">
      {/* glow tím 1-điểm (nguồn sáng tím duy nhất của hero) — parallax nhẹ khi cuộn */}
      <motion.div
        style={{ y: glowY }}
        className="pointer-events-none absolute right-[6%] top-[2%] h-[440px] w-[560px] opacity-60 will-change-transform"
      >
        <div
          className="h-full w-full"
          style={{ background: "radial-gradient(50% 50% at 50% 50%, rgba(124,58,237,0.20), transparent 70%)" }}
        />
      </motion.div>

      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        {/* cột trái — copy canh trái */}
        <div className="text-left">
          <motion.span
            custom={0} variants={fadeUp} initial="hidden" animate="show"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-[12px] font-medium text-ink-medium"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-success shadow-glow-success" />
            Bộ máy kịch bản đang chạy ngay đây · không cần đăng nhập
          </motion.span>

          <motion.h1
            custom={1} variants={fadeUp} initial="hidden" animate="show"
            className="font-display mt-6 max-w-xl text-[clamp(2.4rem,5.4vw,4.25rem)] font-bold leading-[1.0] tracking-[-0.04em] text-ink-high"
          >
            Gõ tên sản phẩm.
            <br />
            <span className="text-gradient">Nhận kịch bản chốt đơn.</span>
          </motion.h1>

          <motion.p
            custom={2} variants={fadeUp} initial="hidden" animate="show"
            className="mt-6 max-w-md text-lg leading-relaxed text-ink-medium"
          >
            Từ 1 ảnh sản phẩm, Vyra viết hook + kịch bản theo timecode, lồng 1 trong 7 giọng
            Việt thật, rồi dựng video 60 giây. Thử ngay bên cạnh — chưa cần tài khoản.
          </motion.p>

          <motion.div
            custom={3} variants={fadeUp} initial="hidden" animate="show"
            className="mt-8 flex flex-wrap items-center gap-3"
          >
            <Link href="/login">
              <Button size="lg" className="gap-2">
                Tạo video đầu tiên <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#winner-loop">
              <Button variant="glass" size="lg">
                Xem cách đo bản thắng
              </Button>
            </a>
          </motion.div>

          <motion.div
            custom={4} variants={fadeUp} initial="hidden" animate="show"
            className="mt-7 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-ink-low"
          >
            <span className="inline-flex items-center gap-1.5"><Clock className="h-4 w-4 text-violet-300" /> ~60 giây / video</span>
            <span className="inline-flex items-center gap-1.5"><Mic className="h-4 w-4 text-violet-300" /> 7 giọng Việt thật</span>
            <span className="inline-flex items-center gap-1.5"><Gift className="h-4 w-4 text-violet-300" /> Tặng 300 credit, không cần thẻ</span>
          </motion.div>
        </div>

        {/* cột phải — playground sống */}
        <ScriptPlayground />
      </div>
    </section>
  );
}
