"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";

// THƯ VIỆN VYRA — tường video thật kiểu MASONRY (Pinterest): mỗi ô lấy ĐÚNG tỉ lệ thật của clip
// (dọc 9:16 hoặc ngang 16:9) nên KHÔNG bao giờ cắt mặt / cắt đầu. Ô cao–thấp xen kẽ tạo bố cục
// lộn xộn có điểm nhấn mà vẫn kín. Đổi clip CHẬM + hiệu ứng cao cấp: crossfade mượt + Ken Burns
// (ảnh "thở" nhẹ). Rê chuột phát đúng clip (không phóng to). Clip lấy từ /showcase/v2 (đều có poster).
type Cat = "Bán hàng" | "KOL ảo" | "Phim & trend" | "Thể loại" | "Sản phẩm";
type Orient = "p" | "l"; // p = dọc 9:16, l = ngang 16:9
type Item = { title: string; note: string; cat: Cat; orient: Orient; clips: string[] };

const V = "/showcase/v2";

// Thứ tự đã trộn dọc/ngang + nhóm để cột masonry cân và trang chủ (18 ô đầu) đa dạng nhất.
const LIB: Item[] = [
  // — 18 ô đầu (trang chủ): trộn mặt KOL, sản phẩm cao cấp, điện ảnh, Tết — điểm nhấn dọc/ngang —
  { title: "KOL review sản phẩm", note: "video chốt đơn", cat: "Bán hàng", orient: "p", clips: [`${V}/idol-vlogger`, `${V}/face-skincare-vanity-warm-lamp`] },
  { title: "Phim điện ảnh", note: "khung hình noir, ánh phim", cat: "Phim & trend", orient: "l", clips: [`${V}/genre-cinematic-film-noir`] },
  { title: "Tết & áo dài", note: "không khí Tết, lễ hội", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-tet-festival-ao-dai`] },
  { title: "Trang sức & vàng", note: "lấp lánh, cận cảnh", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-jewelry-gold-sparkle`] },
  { title: "Siêu anh hùng", note: "hoành tráng, mái nhà hoàng hôn", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-superhero-rooftop-dusk`] },
  { title: "Du lịch & đời sống", note: "b-roll chân thực", cat: "Thể loại", orient: "l", clips: [`${V}/genre-travel-broll-traveler`] },
  { title: "Douyin biến hình", note: "chuyển cảnh, thay đồ", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-douyin-transform-glam`] },
  { title: "Ô tô / xe hơi", note: "showroom, bắt sáng", cat: "Thể loại", orient: "l", clips: [`${V}/genre-car-reveal-showroom`] },
  { title: "Unbox mỹ phẩm", note: "mở hộp, cận cảnh", cat: "Bán hàng", orient: "p", clips: [`${V}/idol-skincare`] },
  { title: "Phim ma / kinh dị", note: "điện ảnh, hù dọa", cat: "Phim & trend", orient: "l", clips: [`${V}/genre-horror-ghost-hallway`] },
  { title: "KOL nam streetwear", note: "phong cách đường phố", cat: "KOL ảo", orient: "p", clips: [`${V}/face-streetwear-golden-hour-male`] },
  { title: "Đu trend bóng đá", note: "cổ vũ, ăn mừng", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-football-fan-celebrate`] },
  { title: "Cafe cozy b-roll", note: "hơi ấm, latte art", cat: "Thể loại", orient: "l", clips: [`${V}/genre-cozy-cafe-latte-broll`] },
  { title: "Gym & thể hình", note: "nam, cơ bắp, mồ hôi", cat: "KOL ảo", orient: "p", clips: [`${V}/face-gym-fitness-male-pump`] },
  { title: "Nhảy đu trend", note: "vũ đạo, bắt trend", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-dance-trend-studio`] },
  { title: "Phim ngắn đêm mưa", note: "kể chuyện, trong xe", cat: "Phim & trend", orient: "l", clips: [`${V}/genre-shortfilm-rainy-car-night`] },
  { title: "Mẹ bỉm & em bé", note: "nội dung gia đình", cat: "KOL ảo", orient: "p", clips: [`${V}/face-young-mom-kitchen-baby`, `${V}/genre-mom-baby-tender`] },
  { title: "Nước hoa", note: "chai xịt, làn sương", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-perfume-bottle-mist`] },
  // — phần còn lại (trang Khám phá hiện hết) —
  { title: "Nam review công nghệ", note: "đập hộp đồ tech", cat: "Bán hàng", orient: "p", clips: [`${V}/face-tech-reviewer-messy-desk-male`, `${V}/prod-tech-earbuds-desk`] },
  { title: "Nàng thơ cafe mưa", note: "nhẹ nhàng, điện ảnh", cat: "KOL ảo", orient: "p", clips: [`${V}/face-pale-elegant-rainy-cafe`] },
  { title: "Bất động sản", note: "walkthrough căn hộ", cat: "Thể loại", orient: "l", clips: [`${V}/genre-real-estate-walkthrough`] },
  { title: "Thời trang đường phố", note: "bắt sóng nhanh", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-street-fashion-walk`] },
  { title: "Quảng cáo shop online", note: "ảnh SP → clip bán hàng", cat: "Bán hàng", orient: "p", clips: [`${V}/prod-fashion-knit-boutique`, `${V}/prod-footwear-sneakers-step`] },
  { title: "Gương mặt KOL cố định", note: "1 mặt, mọi video", cat: "KOL ảo", orient: "p", clips: [`${V}/idol-vlogger`, `${V}/face-girl-next-door-bedroom-vlogger`] },
  { title: "Ẩm thực đường phố", note: "food b-roll, cận cảnh", cat: "Thể loại", orient: "p", clips: [`${V}/genre-cafe-streetfood-eating`] },
  { title: "Máy pha cafe", note: "cận cảnh, bắt sáng", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-appliance-espresso-shot`] },
  { title: "Đồng hồ đeo tay", note: "trên cổ tay, sang", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-watch-wrist-luxury`] },
  { title: "Cô nàng nhà bên", note: "vlog phòng ngủ", cat: "KOL ảo", orient: "p", clips: [`${V}/face-girl-next-door-bedroom-vlogger`] },
  { title: "Kể chuyện bên cửa sổ", note: "tự sự, ánh sáng dịu", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-storyteller-window`] },
  { title: "Túi & phụ kiện da", note: "chất liệu, đường may", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-accessory-leather-bag`] },
  { title: "Yoga & thể thao", note: "chuyển động mượt", cat: "Thể loại", orient: "p", clips: [`${V}/face-morning-yoga-dewy`] },
  { title: "Nấu ăn tại nhà POV", note: "góc nhìn thứ nhất", cat: "Thể loại", orient: "p", clips: [`${V}/genre-home-cooking-pov`] },
  { title: "Đồ ăn vặt ASMR", note: "giòn tan, cận cảnh", cat: "Thể loại", orient: "p", clips: [`${V}/genre-snack-asmr-eating`] },
  { title: "Trang trí & decor", note: "bình hoa, nến thơm", cat: "Sản phẩm", orient: "l", clips: [`${V}/prod-decor-vase-candle`] },
  { title: "Thư sinh tiệm sách", note: "rụt rè, ánh nắng", cat: "KOL ảo", orient: "p", clips: [`${V}/face-bookshop-shy-reader`] },
  { title: "Thú cưng đáng yêu", note: "không cần người", cat: "Thể loại", orient: "p", clips: [`${V}/genre-cute-pet-no-person`] },
  { title: "Hoạt hình 3D", note: "nhân vật dễ thương", cat: "Phim & trend", orient: "p", clips: [`${V}/genre-animation-3d-character`] },
  { title: "Chốt đơn livestream", note: "hook 3 giây", cat: "Bán hàng", orient: "p", clips: [`${V}/face-skincare-vanity-warm-lamp`] },
  { title: "Ảnh sản phẩm thời trang", note: "nền sạch, lên sàn", cat: "Sản phẩm", orient: "p", clips: [`${V}/prod-fashion-knit-boutique`] },
  { title: "Giày sneaker", note: "xoay 360, bắt sáng", cat: "Sản phẩm", orient: "p", clips: [`${V}/prod-footwear-sneakers-step`] },
  { title: "Tai nghe & đồ tech", note: "cận cảnh chi tiết", cat: "Sản phẩm", orient: "p", clips: [`${V}/prod-tech-earbuds-desk`] },
];

export const LIBRARY_CATS: Cat[] = ["Bán hàng", "KOL ảo", "Phim & trend", "Thể loại", "Sản phẩm"];

function LibraryTile({ item, i }: { item: Item; i: number }) {
  const [idx, setIdx] = useState(0);
  const [hover, setHover] = useState(false);
  const ref = useRef<HTMLVideoElement>(null);

  // Tự xoay clip khi KHÔNG hover — CHẬM (5.2–9.2s), chu kỳ lệch nhau theo i để không đổi đồng loạt.
  useEffect(() => {
    if (hover || item.clips.length < 2) return;
    const period = 5200 + (i % 6) * 800;
    const id = setInterval(() => setIdx((v) => (v + 1) % item.clips.length), period);
    return () => clearInterval(id);
  }, [hover, item.clips.length, i]);

  // KHUNG = đúng tỉ lệ thật của clip → object-cover gần như không cắt gì (mọi clip đã chuẩn 9:16 / 16:9).
  const aspect = item.orient === "p" ? "aspect-[9/16]" : "aspect-[16/9]";
  // Ken Burns lệch pha theo tile (delay âm) để mỗi ô "thở" khác nhịp, không đồng loạt.
  const kbDelay = `-${(i * 3.5) % 24}s`;

  return (
    <div
      className={cn("group relative block w-full overflow-hidden rounded-2xl glass-bordered", aspect)}
      onMouseEnter={() => { setHover(true); ref.current?.play().catch(() => {}); }}
      onMouseLeave={() => { setHover(false); const v = ref.current; if (v) { v.pause(); v.currentTime = 0; } }}
    >
      {/* Các lớp ảnh xếp chồng — đổi clip = crossfade opacity 1.6s (mượt cao cấp). Mỗi lớp Ken Burns nhẹ. */}
      {item.clips.map((c, k) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={c}
          src={`${c}.jpg`}
          alt=""
          loading="lazy"
          decoding="async"
          style={{ animationDelay: kbDelay }}
          className={cn(
            "absolute inset-0 h-full w-full animate-kenburns object-cover transition-opacity duration-[1600ms] ease-[cubic-bezier(0.4,0,0.2,1)]",
            k === idx ? "opacity-100" : "opacity-0",
          )}
        />
      ))}

      {/* video phát khi hover (KHÔNG phóng to) */}
      <video
        ref={ref}
        key={`${item.clips[idx]}-v`}
        src={`${item.clips[idx]}.mp4`}
        poster={`${item.clips[idx]}.jpg`}
        muted
        loop
        playsInline
        preload="none"
        className={cn(
          "absolute inset-0 h-full w-full object-cover transition-opacity duration-500",
          hover ? "opacity-100" : "opacity-0",
        )}
      />

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base/95 via-bg-base/10 to-transparent" />
      {/* viền sáng tím khi hover — điểm nhấn nhẹ, không zoom */}
      <div className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-inset ring-white/0 transition duration-500 group-hover:ring-violet-400/40" />

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
 * `limit` — số ô hiển thị (trang chủ giới hạn ~18). Bỏ trống = hiện hết.
 * `filter` — lọc theo nhóm (trang Khám phá dùng tab). "Tất cả" = không lọc.
 * Bố cục MASONRY (CSS columns): ô dọc cao, ô ngang thấp → xen kẽ lộn xộn mà kín, KHÔNG cắt mặt.
 */
export function VideoLibrary({ limit, filter }: { limit?: number; filter?: Cat | "Tất cả" }) {
  const filtered = filter && filter !== "Tất cả" ? LIB.filter((it) => it.cat === filter) : LIB;
  const items = limit ? filtered.slice(0, limit) : filtered;
  return (
    <div className="gap-2.5 [column-fill:balance] columns-2 sm:gap-3 sm:columns-3 lg:columns-4 xl:columns-5">
      {items.map((it, i) => (
        <div key={it.title} className="mb-2.5 break-inside-avoid sm:mb-3">
          <LibraryTile item={it} i={i} />
        </div>
      ))}
    </div>
  );
}

/** Khối THƯ VIỆN trên trang chủ — tiêu đề + tường video + lối sang trang Khám phá. */
export function LibrarySection() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-12 sm:py-16 lg:py-24">
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
        <VideoLibrary limit={18} />
      </div>
    </section>
  );
}
