import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/reveal";

// Mirror manifesto "SẴN SÀNG · KHỞI TẠO · TỎA SÁNG" của autovis, giọng Vyra.
// KHÔNG dùng chữ-nền khổng lồ (motif đó để dành cho tagline cuối) — dùng divider + 3-nhịp nền sạch.
export function Manifesto() {
  return (
    <section className="px-4 py-28 lg:py-32">
      <Reveal className="mx-auto max-w-3xl text-center">
        <div className="mx-auto mb-8 h-px max-w-xs bg-gradient-to-r from-transparent via-violet-500/70 to-transparent" />
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
          Tải ảnh · Chọn giọng · Ra video
        </p>
        <h2 className="mt-4 font-display text-[clamp(1.9rem,5vw,3rem)] font-bold leading-[1.06] tracking-tight text-ink-high">
          Studio video của bạn, <span className="text-gradient">không cần studio.</span>
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-ink-medium">
          Không thiết bị, không ekip, không lịch quay. Bạn đưa ý tưởng và một tấm ảnh sản phẩm —
          Vyra lo kịch bản, giọng Việt thật, phụ đề khớp khung và bản dựng 60 giây. Phần còn lại,
          để số liệu chọn bản thắng.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/login">
            <Button size="lg">Tạo video đầu tiên</Button>
          </Link>
          <a href="#nang-luc">
            <Button variant="glass" size="lg">Xem 6 năng lực</Button>
          </a>
        </div>
      </Reveal>
    </section>
  );
}
