"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// THƯ VIỆN VYRA — tường video thật (9:16) kiểu autovis, nhưng tile ĐỘNG: mỗi ô tự đổi
// qua nhiều clip, rê chuột thì phát đúng clip đang hiện + phóng to nhẹ. Clip lấy từ /showcase/v2
// (đều có poster .jpg). Text VN cứng (giống model-wall) — đây là khối showcase, không qua i18n.
type Cat = "Bán hàng" | "KOL ảo" | "Thể loại" | "Sản phẩm";
type Item = { title: string; note: string; cat: Cat; clips: string[] };

const V = "/showcase/v2";
const LIB: Item[] = [
  { title: "KOL review sản phẩm", note: "video chốt đơn", cat: "Bán hàng", clips: [`${V}/idol-vlogger`, `${V}/face-skincare-vanity-warm-lamp`] },
  { title: "Quảng cáo shop online", note: "ảnh SP → clip bán hàng", cat: "Bán hàng", clips: [`${V}/prod-fashion-knit-boutique`, `${V}/prod-footwear-sneakers-step`] },
  { title: "Unbox mỹ phẩm", note: "mở hộp, cận cảnh", cat: "Bán hàng", clips: [`${V}/idol-skincare`, `${V}/prod-decor-vase-candle`] },
  { title: "Gương mặt KOL cố định", note: "1 mặt, mọi video", cat: "KOL ảo", clips: [`${V}/idol-vlogger`, `${V}/face-girl-next-door-bedroom-vlogger`] },
  { title: "KOL nam công nghệ", note: "review đồ tech", cat: "KOL ảo", clips: [`${V}/face-tech-reviewer-messy-desk-male`, `${V}/face-streetwear-golden-hour-male`] },
  { title: "Mẹ bỉm & em bé", note: "nội dung gia đình", cat: "KOL ảo", clips: [`${V}/face-young-mom-kitchen-baby`, `${V}/genre-mom-baby-tender`] },
  { title: "Đu trend đường phố", note: "bắt sóng nhanh", cat: "Thể loại", clips: [`${V}/genre-street-fashion-walk`, `${V}/face-streetwear-golden-hour-male`] },
  { title: "Ẩm thực đường phố", note: "food b-roll", cat: "Thể loại", clips: [`${V}/genre-cafe-streetfood-eating`, `${V}/genre-home-cooking-pov`] },
  { title: "Phim ngắn / kể chuyện", note: "điện ảnh, đêm mưa", cat: "Thể loại", clips: [`${V}/genre-shortfilm-rainy-car-night`, `${V}/genre-storyteller-window`] },
  { title: "Du lịch & đời sống", note: "b-roll chân thực", cat: "Thể loại", clips: [`${V}/genre-travel-broll-traveler`, `${V}/genre-cozy-cafe-latte-broll`] },
  { title: "Bất động sản", note: "walkthrough căn hộ", cat: "Thể loại", clips: [`${V}/genre-real-estate-walkthrough`, `${V}/genre-cute-pet-no-person`] },
  { title: "Yoga & thể thao", note: "chuyển động mượt", cat: "Thể loại", clips: [`${V}/face-morning-yoga-dewy`, `${V}/face-pale-elegant-rainy-cafe`] },
  { title: "Ảnh sản phẩm thời trang", note: "nền sạch, lên sàn", cat: "Sản phẩm", clips: [`${V}/prod-fashion-knit-boutique`, `${V}/prod-accessory-leather-bag`] },
  { title: "Tai nghe & đồ tech", note: "cận cảnh chi tiết", cat: "Sản phẩm", clips: [`${V}/prod-tech-earbuds-desk`, `${V}/prod-appliance-espresso-shot`] },
  { title: "Giày & phụ kiện", note: "xoay 360, bắt sáng", cat: "Sản phẩm", clips: [`${V}/prod-footwear-sneakers-step`, `${V}/prod-accessory-leather-bag`] },
];

export const LIBRARY_CATS: Cat[] = ["Bán hàng", "KOL ảo", "Thể loại", "Sản phẩm"];

function LibraryTile({ item, i }: { item: Item; i: number }) {
  const [idx, setIdx] = useState(0);
  const [hover, setHover] = useState(false);
  const ref = useRef<HTMLVideoElement>(null);

  // Tự xoay clip khi KHÔNG hover (đang hover thì giữ để phát trọn clip). Chu kỳ lệch nhau
  // theo i để các ô không đổi cùng lúc → tường sống động, không "nhấp nháy đồng loạt".
  useEffect(() => {
    if (hover || item.clips.length < 2) return;
    const period = 3800 + (i % 6) * 520;
    const id = setInterval(() => setIdx((v) => (v + 1) % item.clips.length), period);
    return () => clearInterval(id);
  }, [hover, item.clips.length, i]);

  const clip = item.clips[idx];

  return (
    <div
      className="group relative aspect-[9/16] overflow-hidden rounded-2xl glass-bordered"
      onMouseEnter={() => { setHover(true); ref.current?.play().catch(() => {}); }}
      onMouseLeave={() => { setHover(false); const v = ref.current; if (v) { v.pause(); v.currentTime = 0; } }}
    >
      {/* lớp media zoom nhẹ khi hover */}
      <div className="absolute inset-0 transition-transform duration-[900ms] ease-out group-hover:scale-[1.08]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          key={clip}
          src={`${clip}.jpg`}
          alt=""
          loading="lazy"
          decoding="async"
          className="h-full w-full animate-in fade-in object-cover duration-700"
        />
        <video
          ref={ref}
          key={`${clip}-v`}
          src={`${clip}.mp4`}
          poster={`${clip}.jpg`}
          muted
          loop
          playsInline
          preload="none"
          className={cn(
            "absolute inset-0 h-full w-full object-cover transition-opacity duration-300",
            hover ? "opacity-100" : "opacity-0",
          )}
        />
      </div>

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/15 to-transparent" />

      {/* chấm báo số clip trong ô (tile động) */}
      {item.clips.length > 1 && (
        <div className="pointer-events-none absolute right-2.5 top-2.5 flex gap-1">
          {item.clips.map((c, k) => (
            <span key={c} className={cn("h-1 w-1 rounded-full transition-colors", k === idx ? "bg-white/90" : "bg-white/30")} />
          ))}
        </div>
      )}

      <div className="pointer-events-none absolute inset-x-0 bottom-0 p-3">
        <div className="font-display text-sm font-semibold leading-tight text-ink-high">{item.title}</div>
        <div className="mt-0.5 text-[11px] text-ink-low">{item.note}</div>
      </div>
    </div>
  );
}

/**
 * `limit` — số ô hiển thị (trang chủ giới hạn ~10). Bỏ trống = hiện hết.
 * `filter` — lọc theo nhóm (trang Khám phá dùng tab). "Tất cả" = không lọc.
 */
export function VideoLibrary({ limit, filter }: { limit?: number; filter?: Cat | "Tất cả" }) {
  const filtered = filter && filter !== "Tất cả" ? LIB.filter((it) => it.cat === filter) : LIB;
  const items = limit ? filtered.slice(0, limit) : filtered;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((it, i) => (
        <LibraryTile key={it.title} item={it} i={i} />
      ))}
    </div>
  );
}

/** Khối THƯ VIỆN trên trang chủ — tiêu đề + tường video + lối sang trang Khám phá. */
export function LibrarySection() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
      <Reveal>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-xl">
            <FilmLabel>Thư viện Vyra</FilmLabel>
            <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
              Video thật, <span className="text-gradient italic">đủ mọi thể loại</span>, dựng bằng Vyra.
            </h2>
          </div>
          <Link
            href="/kham-pha"
            className="inline-flex w-fit items-center gap-1.5 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-medium text-ink-medium transition hover:border-violet-400/30 hover:text-ink-high"
          >
            Xem tất cả thư viện
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </Reveal>
      <div className="mt-9">
        <VideoLibrary limit={10} />
      </div>
    </section>
  );
}
