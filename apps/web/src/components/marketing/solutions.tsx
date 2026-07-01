"use client";

import Link from "next/link";
import { UserSquare2, PenLine, Coins, ShieldCheck, ArrowUpRight, type LucideIcon } from "lucide-react";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// "Vyra giải quyết gì cho người bán" — đối ứng khối 'solutions' của autovis nhưng MẠNH hơn:
// đóng khung theo NỖI ĐAU thật của người bán → cách Vyra lo, gắn thẳng vào 2 con hào
// (thanh toán bản địa + render lỗi không trừ tiền). Không sao chép, là nét riêng Vyra.
type Sol = { icon: LucideIcon; pain: string; title: string; desc: string };

const SOLUTIONS: Sol[] = [
  {
    icon: UserSquare2,
    pain: "Không có người mẫu, ngại lên hình",
    title: "KOL ảo mặt Việt, dùng cả năm",
    desc: "Dựng một gương mặt KOL một lần, tái dùng miễn phí cho mọi video. Không thuê người, không lộ mặt bạn.",
  },
  {
    icon: PenLine,
    pain: "Không biết viết kịch bản bán hàng",
    title: "AI viết hook chốt đơn",
    desc: "Hook 3 giây + kịch bản theo timecode (mở → nỗi đau → lợi ích → chốt). Bạn chỉ chỉnh lại lời cho hợp shop.",
  },
  {
    icon: Coins,
    pain: "Thuê KOC đắt, làm được ít video",
    title: "Tự dựng hàng loạt, rẻ hơn nhiều",
    desc: "Một sản phẩm ra nhiều biến thể nam/nữ/hook trong một lần. Chi phí bằng một phần nhỏ so với thuê người.",
  },
  {
    icon: ShieldCheck,
    pain: "Sợ mất tiền, sợ tài khoản nước ngoài",
    title: "Trả tiền Việt, không mất oan",
    desc: "Nạp MoMo/chuyển khoản, render lỗi không trừ tiền, xu mua không hết hạn. Minh bạch từng credit.",
  },
];

export function Solutions() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
      <Reveal>
        <div className="max-w-2xl">
          <FilmLabel>Vyra lo trọn gói</FilmLabel>
          <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
            Người bán cần gì, <span className="text-gradient italic">Vyra lo nấy.</span>
          </h2>
          <p className="mt-4 text-ink-medium">
            Đối thủ dừng ở "tạo video". Vyra lo trọn khâu: từ ý tưởng → kịch bản → KOL → giọng Việt →
            xuất đủ tỉ lệ sẵn đăng. Bạn chỉ việc dán link sản phẩm.
          </p>
        </div>
      </Reveal>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {SOLUTIONS.map((s, i) => (
          <Reveal key={s.title} delay={0.05 * i}>
            <div className="group flex h-full flex-col rounded-3xl glass-bordered p-6 transition-all duration-300 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30">
              <span className="grid h-11 w-11 place-items-center rounded-2xl border border-violet-400/20 bg-violet-500/10 text-violet-300 transition-colors group-hover:bg-violet-500/20">
                <s.icon className="h-5 w-5" />
              </span>
              <div className="mt-4 text-[11px] font-medium uppercase tracking-wide text-ink-low">{s.pain}</div>
              <div className="mt-1 font-display text-lg font-bold leading-tight text-ink-high">{s.title}</div>
              <p className="mt-2 text-sm leading-relaxed text-ink-medium">{s.desc}</p>
            </div>
          </Reveal>
        ))}
      </div>

      <Reveal delay={0.1}>
        <div className="mt-6">
          <Link
            href="/kham-pha"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-violet-300 transition hover:text-violet-200"
          >
            Xem video thật Vyra đã dựng
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
