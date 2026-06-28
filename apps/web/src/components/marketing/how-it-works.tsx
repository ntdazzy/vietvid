"use client";

import { motion } from "framer-motion";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";

const STEPS = [
  { t: "Tải 1 ảnh / dán link", d: "Kéo thả ảnh, hoặc dán link Shopee/TikTok-Shop để Vyra tự bóc ảnh + giá + tên." },
  { t: "Chọn góc & giọng", d: "1 trong 6 góc chốt đơn, 1 trong 7 giọng Việt. Sửa từng câu kịch bản." },
  { t: "Vyra dựng video 60s", d: "Lồng giọng, ghép phụ đề khớp khung, xuất đủ 3 tỉ lệ. Khoảng 60 giây." },
  { t: "Đo click, nhân bản bản thắng", d: "Mỗi biến thể một short-link. Đo click thật, xếp hạng, clone bản bán được." },
];

export function HowItWorks() {
  return (
    <div className="mx-auto max-w-6xl px-4">
      <SectionHeading
        align="center"
        eyebrow="Từ ảnh tới đơn"
        title={<>Bốn bước. <span className="text-gradient">Không cần biết dựng phim.</span></>}
      />
      <div className="relative mt-12 grid gap-6 md:grid-cols-4">
        {/* đường nối "vẽ" ngang (desktop) */}
        <motion.div
          aria-hidden
          initial={{ scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          style={{ transformOrigin: "left" }}
          className="absolute left-0 right-0 top-12 hidden h-px bg-gradient-to-r from-violet-500/50 via-violet-500/30 to-transparent md:block"
        />
        {STEPS.map((s, i) => (
          <Reveal key={s.t} delay={0.1 * i}>
            <div className="glass relative flex h-full flex-col gap-2 rounded-2xl p-5">
              <span className="font-display text-4xl font-extrabold text-gradient">{i + 1}</span>
              <h3 className="font-display text-base font-semibold text-ink-high">{s.t}</h3>
              <p className="text-sm text-ink-low">{s.d}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </div>
  );
}
