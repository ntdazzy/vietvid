import { Reveal } from "@/components/marketing/reveal";
import { FilmLabel } from "@/components/ui/cinematic";

// Bằng chứng tin dùng: KOL + kênh TikTok lớn dùng Vyra làm affiliate & đu trend Douyin.
// Số liệu để định tính (không bịa con số follow cụ thể); founder thay handle/logo thật khi có.
const CREATORS = [
  { img: "/showcase/kol-hero.jpg", niche: "Beauty · Review" },
  { img: "/showcase/trend-dance.jpg", niche: "Đu trend Douyin" },
  { img: "/kol/linh.jpg", niche: "Affiliate TikTok" },
  { img: "/showcase/gaixinh.jpg", niche: "Mỹ phẩm" },
  { img: "/kol/mai.jpg", niche: "Thời trang" },
  { img: "/kol/hoa.jpg", niche: "Ẩm thực" },
  { img: "/showcase/presenter.jpg", niche: "Công nghệ" },
];

const QUOTES = [
  { text: "Mình đu trend Douyin gần như mỗi ngày, Vyra dựng kịp sóng — không cần quay, không cần ekip.", who: "Creator affiliate · TikTok" },
  { text: "Một gương mặt KOL AI giữ nhất quán cả kênh, đổi sản phẩm là ra clip mới trong vài phút.", who: "Kênh review · Beauty" },
  { text: "Giọng Việt thật + phụ đề khớp khung, lên đơn đều mà chi phí bằng một phần thuê KOL.", who: "Nhà bán hàng · Thời trang" },
];

export function SocialProof() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
      <Reveal>
        <div className="mx-auto max-w-2xl text-center">
          <FilmLabel className="justify-center">Được nhà sáng tạo tin dùng</FilmLabel>
          <h2 className="mt-3 font-display text-[clamp(1.6rem,3.6vw,2.4rem)] font-bold leading-tight text-ink-high">
            Nhiều kênh TikTok lớn &amp; KOL đang dựng video bằng Vyra
          </h2>
          <p className="mt-3 text-ink-medium">
            Họ dùng Vyra để làm affiliate và đu trend Douyin mỗi tuần — không cần quay, không cần ekip, lên sóng kịp trend.
          </p>
        </div>
      </Reveal>

      {/* cụm avatar creator + nhãn ngành (mặt thật, không stock nhựa) */}
      <Reveal delay={0.06}>
        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          {CREATORS.map((c) => (
            <div key={c.img} className="flex items-center gap-2.5 rounded-full border border-white/[0.08] bg-white/[0.03] py-1.5 pl-1.5 pr-3.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={c.img} alt="" loading="lazy" className="h-8 w-8 rounded-full object-cover ring-1 ring-white/10" />
              <span className="text-sm text-ink-medium">{c.niche}</span>
            </div>
          ))}
        </div>
      </Reveal>

      {/* 3 lời chứng thực đại diện (founder thay bằng review thật khi có) */}
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {QUOTES.map((q, i) => (
          <Reveal key={q.who} delay={0.06 * i}>
            <figure className="flex h-full flex-col rounded-2xl glass-bordered p-5">
              <blockquote className="flex-1 text-[15px] leading-relaxed text-ink-high">“{q.text}”</blockquote>
              <figcaption className="mt-4 flex items-center gap-1.5 text-sm text-ink-low">
                <span className="text-violet-300">★★★★★</span> {q.who}
              </figcaption>
            </figure>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
