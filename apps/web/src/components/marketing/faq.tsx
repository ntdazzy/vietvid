"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { SectionHeading } from "@/components/marketing/section-heading";
import { Reveal } from "@/components/marketing/reveal";
import { cn } from "@/lib/utils/cn";

const QA: { q: string; a: string }[] = [
  { q: "Vyra là gì?", a: "Vyra biến 1 ảnh sản phẩm thành video quảng cáo 60 giây với giọng Việt thật — tự viết kịch bản, lồng tiếng, ghép phụ đề và dựng video, không cần máy quay hay ekip." },
  { q: "Tôi không biết dựng video có dùng được không?", a: "Được. Bạn chỉ cần tải 1 ảnh (hoặc dán link sàn để Vyra tự bóc), chọn góc và giọng, phần còn lại Vyra lo. Bốn bước, khoảng 60 giây." },
  { q: "Giọng đọc có tự nhiên như người thật không?", a: "Có 7 giọng Việt cá tính (Mai, Linh, Trang, Bống, Khoa, Hùng, Tú) — trẻ trung, nhẹ nhàng, trầm ấm, dí dỏm. Bạn nghe thử từng giọng ngay trong app trước khi tạo." },
  { q: "Chi phí tính thế nào?", a: "Trả theo credit, thấy trước số credit mỗi video trước khi tạo. Đăng ký tặng 300 credit, không cần thẻ. Chỉ trừ khi dùng, và hoàn 100% nếu lỗi hệ thống." },
  { q: "Lỗi hệ thống có được hoàn tiền không?", a: "Có. Vyra chỉ tạm giữ credit khi tạo, dùng bao nhiêu tính bấy nhiêu; nếu render lỗi do hệ thống, hoàn lại 100%." },
  { q: "Video có watermark không?", a: "Gói trả phí xuất video không watermark. Bạn cũng xuất được đủ 3 tỉ lệ: dọc 9:16, vuông 1:1, ngang 16:9." },
  { q: "Vyra dựng được những loại video nào?", a: "Quảng cáo bán hàng, KOL AI review, lookbook, mở hộp, bắt trend, cảm nhận khách, so sánh sản phẩm… cùng một quy trình." },
  { q: "Có API để tích hợp vào hệ thống của tôi không?", a: "Có. Vyra cung cấp API B2B (POST /api/v1/videos với X-API-Key) và webhook báo khi video xong, ký HMAC để xác thực." },
];

function Item({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <button
      type="button"
      onClick={() => setOpen((v) => !v)}
      className="w-full rounded-2xl border border-white/[0.08] bg-white/[0.02] p-5 text-left transition-colors hover:border-white/[0.16]"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="font-medium text-ink-high">{q}</span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-violet-300 transition-transform", open && "rotate-180")} />
      </div>
      <div className={cn("grid transition-all duration-300", open ? "mt-3 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")}>
        <p className="overflow-hidden text-sm leading-relaxed text-ink-low">{a}</p>
      </div>
    </button>
  );
}

export function Faq() {
  return (
    <section id="faq" className="mx-auto max-w-3xl px-4 py-24 lg:py-28">
      <SectionHeading
        align="center"
        eyebrow="Hỗ trợ"
        title={<>Câu hỏi <span className="text-gradient">thường gặp</span></>}
      />
      <div className="mt-10 flex flex-col gap-3">
        {QA.map((x, i) => (
          <Reveal key={x.q} delay={0.04 * i}>
            <Item q={x.q} a={x.a} />
          </Reveal>
        ))}
      </div>
    </section>
  );
}
