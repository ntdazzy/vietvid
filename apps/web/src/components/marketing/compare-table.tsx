"use client";

import { Check } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";
import { SectionHeading } from "@/components/marketing/section-heading";
import { cn } from "@/lib/utils/cn";

// So sánh ĐỊNH TÍNH (không bịa số). Cột Vyra sáng.
const ROWS: [string, string, string, string][] = [
  ["Giọng Việt thật", "Tùy diễn viên", "Giọng máy lơ lớ", "7 giọng Việt cá tính"],
  ["Phụ đề khớp khung", "Canh tay, lệch", "Dựa ASR, sai chính tả", "Timing từ kịch bản, 0 lỗi"],
  ["Biết video nào ra đơn", "Đoán", "Không có", "Đo click thật, xếp hạng"],
  ["Thời gian / video", "Vài ngày", "Vài chục phút", "~60 giây"],
  ["Dán link sàn tự bóc", "Không", "Không", "Shopee / TikTok-Shop / Lazada"],
];

export function CompareTable() {
  return (
    <div className="mx-auto max-w-5xl px-4">
      <SectionHeading
        align="center"
        eyebrow="Vì sao đổi sang Vyra"
        title={<>Cùng một video. <span className="text-gradient">Khác nhau ở chỗ ra đơn.</span></>}
      />
      <Reveal className="mt-10 overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left">
              <th className="p-3 font-medium text-ink-low">Tiêu chí</th>
              <th className="p-3 font-medium text-ink-low">Tự quay / agency</th>
              <th className="p-3 font-medium text-ink-low">Tool nước ngoài</th>
              <th className="rounded-t-xl bg-violet-500/[0.08] p-3 font-bold text-ink-high ring-1 ring-violet-400/20">
                Vyra
              </th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map(([crit, a, b, v], i) => (
              <tr key={crit}>
                <td className="border-t border-white/[0.06] p-3 font-medium text-ink-medium">{crit}</td>
                <td className="border-t border-white/[0.06] p-3 text-ink-low">{a}</td>
                <td className="border-t border-white/[0.06] p-3 text-ink-low">{b}</td>
                <td className={cn(
                  "border-t border-violet-400/20 bg-violet-500/[0.06] p-3 font-semibold text-ink-high",
                  i === ROWS.length - 1 && "rounded-b-xl",
                )}>
                  <span className="inline-flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-success" /> {v}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Reveal>
    </div>
  );
}
