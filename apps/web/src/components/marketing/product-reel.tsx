"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { HoverVideo } from "@/components/ui/hover-video";

// "Ảnh sản phẩm → video bán hàng" — 6 clip SP THẬT v2. Dọc 9:16 → ô cao; ngang 16:9 → ô rộng.
// Khối thương mại: seller thấy ngay "đưa ảnh SP vào, ra clip quảng cáo". Hardcode nhãn Việt.
const PRODUCTS: { key: string; label: string; note: string; wide?: boolean }[] = [
  { key: "prod-fashion-knit-boutique", label: "Thời trang · áo len", note: "từ kệ shop ra clip" },
  { key: "prod-accessory-leather-bag", label: "Túi da · phụ kiện", note: "cận chất liệu, đường may", wide: true },
  { key: "prod-tech-earbuds-desk", label: "Tai nghe · công nghệ", note: "đặc tả sản phẩm" },
  { key: "prod-appliance-espresso-shot", label: "Máy pha cà phê", note: "rót shot, hơi nóng", wide: true },
  { key: "prod-footwear-sneakers-step", label: "Giày sneaker", note: "bước chân, chi tiết" },
  { key: "prod-decor-vase-candle", label: "Décor · trang trí", note: "không gian sống", wide: true },
];

export function ProductReel() {
  return (
    <section className="mx-auto max-w-[1600px] px-4 py-20 lg:py-24">
      <Reveal>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-xl">
            <FilmLabel>Bán hàng · Affiliate</FilmLabel>
            <h2 className="mt-3 font-display text-[clamp(1.75rem,4vw,2.6rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
              Ảnh sản phẩm. <span className="text-gradient italic">Ra video bán hàng.</span>
            </h2>
          </div>
          <p className="max-w-xs text-sm text-ink-low sm:text-right">
            Đưa 1 tấm ảnh sản phẩm, Vyra dựng clip quảng cáo 9:16 hoặc 16:9. Gắn link, lên đơn.
          </p>
        </div>
      </Reveal>

      <div className="mt-9 grid auto-rows-[150px] grid-flow-dense grid-cols-2 gap-3 sm:auto-rows-[170px] sm:grid-cols-4 lg:auto-rows-[200px] lg:grid-cols-4 lg:gap-4">
        {PRODUCTS.map((p, i) => {
          const src = `/showcase/v2/${p.key}`;
          return (
            <Reveal key={p.key} delay={0.03 * i} className={p.wide ? "col-span-2" : "row-span-2"}>
              <Link
                href="/login"
                className="group relative block h-full overflow-hidden rounded-2xl glass-bordered transition-all duration-200 hover:-translate-y-1 hover:ring-1 hover:ring-violet-400/30"
              >
                <HoverVideo
                  poster={`${src}.jpg`}
                  video={`${src}.mp4`}
                  alt={p.label}
                  badge={false}
                  objectClass="object-center"
                  className="absolute inset-0 h-full w-full opacity-[0.9] transition-opacity duration-500 group-hover:opacity-100"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-bg-base via-bg-base/25 to-transparent" />
                <div className="pointer-events-none absolute inset-x-0 bottom-0 p-3.5">
                  <div className="font-display text-sm font-semibold leading-tight text-ink-high">{p.label}</div>
                  <div className="mt-0.5 text-[11px] text-ink-low">{p.note}</div>
                </div>
                <span className="pointer-events-none absolute right-2.5 top-2.5 grid h-6 w-6 place-items-center rounded-full bg-black/40 opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
                  <span className="ml-0.5 block h-0 w-0 border-y-[5px] border-l-[8px] border-y-transparent border-l-white/90" />
                </span>
              </Link>
            </Reveal>
          );
        })}
      </div>

      <Reveal delay={0.1}>
        <div className="mt-8 flex justify-center">
          <Link href="/login">
            <Button className="gap-1.5">Tạo video bán hàng</Button>
          </Link>
        </div>
      </Reveal>
    </section>
  );
}
