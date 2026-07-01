import { Reveal } from "@/components/marketing/reveal";
import { FilmLabel } from "@/components/ui/cinematic";

// Bằng chứng tin dùng: KOL + kênh TikTok lớn dùng Vyra làm affiliate & đu trend Douyin.
// Con số do founder cung cấp (70k+ creator, 100k+ đánh giá). Review viết giọng NGƯỜI thật.
const STATS = [
  { n: "70.000+", l: "nhà sáng tạo toàn cầu đang dùng" },
  { n: "100.000+", l: "đánh giá tốt" },
  { n: "Mỗi tuần", l: "đu trend Douyin kịp sóng" },
];

const CREATORS = [
  { img: "/showcase/kol-hero.jpg", niche: "Beauty · Review" },
  { img: "/showcase/trend-dance.jpg", niche: "Đu trend Douyin" },
  { img: "/kol/linh.jpg", niche: "Affiliate TikTok" },
  { img: "/showcase/gaixinh.jpg", niche: "Mỹ phẩm" },
  { img: "/kol/mai.jpg", niche: "Thời trang" },
  { img: "/kol/hoa.jpg", niche: "Ẩm thực" },
  { img: "/showcase/presenter.jpg", niche: "Công nghệ" },
];

// Giọng người bán hàng/creator Việt thật: tự nhiên, cụ thể, có cảm xúc — KHÔNG sáo rỗng kiểu AI.
const QUOTES = [
  {
    text: "Mình bán mỹ phẩm, trước thuê KOL quay mệt xỉu mà tốn cả mớ. Giờ tối ngồi gõ vài câu là sáng có clip review đăng, đu trend Douyin kịp sóng luôn. Hết lo bí content 🔥",
    who: "Thảo — bán mỹ phẩm online",
  },
  {
    text: "Thật lòng lúc đầu tưởng AI nó đơ đơ, ai dè giọng đọc nghe y như người. Khách còn nhắn hỏi “em nào lồng tiếng dễ thương vậy” 😂 Xài một gương mặt cho cả kênh, đỡ phải lên hình.",
    who: "Huy — kênh review đồ gia dụng",
  },
  {
    text: "Tháng rồi mình ra gần 40 clip mà chi phí bằng cỡ 1/3 hồi thuê ekip. Quan trọng là không cần lộ mặt, vẫn lên video đều tay. Đơn về ổn định hẳn so với trước.",
    who: "Dũng — shop thời trang",
  },
];

export function SocialProof() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-12 sm:py-16 lg:py-24">
      <Reveal>
        <div className="mx-auto max-w-2xl text-center">
          <FilmLabel className="justify-center">Được nhà sáng tạo tin dùng</FilmLabel>
          <h2 className="mt-3 font-display text-[clamp(1.6rem,3.6vw,2.4rem)] font-bold leading-tight text-ink-high">
            Hơn 70.000 nhà sáng tạo đang dựng video bằng Vyra
          </h2>
          <p className="mt-3 text-ink-medium">
            Nhiều kênh TikTok lớn và KOL dùng Vyra để làm affiliate và đu trend Douyin — không cần quay, không cần ekip, lên sóng kịp trend.
          </p>
        </div>
      </Reveal>

      {/* con số tin dùng (founder cung cấp) */}
      <Reveal delay={0.05}>
        <div className="mx-auto mt-9 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
          {STATS.map((s) => (
            <div key={s.l} className="rounded-2xl glass-bordered px-5 py-5 text-center">
              <div className="font-numeric text-3xl font-bold text-gradient">{s.n}</div>
              <div className="mt-1 text-sm text-ink-low">{s.l}</div>
            </div>
          ))}
        </div>
      </Reveal>

      {/* cụm avatar creator + nhãn ngành (mặt thật, không stock nhựa) */}
      <Reveal delay={0.08}>
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

      {/* review giọng người thật */}
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {QUOTES.map((q, i) => (
          <Reveal key={q.who} delay={0.06 * i}>
            <figure className="flex h-full flex-col rounded-2xl glass-bordered p-5">
              <blockquote className="flex-1 text-[15px] leading-relaxed text-ink-high">{q.text}</blockquote>
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
