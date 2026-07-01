"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { SiteHeader } from "@/components/marketing/site-header";
import { ScrollToTop } from "@/components/marketing/scroll-to-top";
import { FilmLabel } from "@/components/ui/cinematic";
import { Button } from "@/components/ui/button";
import { VideoLibrary, LIBRARY_CATS } from "@/components/marketing/video-library";
import { cn } from "@/lib/utils/cn";

// Trang KHÁM PHÁ — thư viện video đầy đủ kiểu autovis/home, nhưng nét riêng Vyra: tile động
// (tự đổi clip + hover phát + zoom) + lọc theo nhóm việc của người bán. Không sao chép layout đối thủ.
const TABS = ["Tất cả", ...LIBRARY_CATS] as const;

export default function KhamPhaPage() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Tất cả");

  return (
    <div className="min-h-dvh mesh-bg">
      <SiteHeader />
      <ScrollToTop />

      <div className="mx-auto max-w-[1600px] px-4 pb-20 pt-28 lg:pt-32">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-ink-low transition hover:text-ink-medium"
        >
          <ArrowLeft className="h-4 w-4" /> Về trang chủ
        </Link>

        <div className="mt-6 max-w-2xl">
          <FilmLabel>Khám phá</FilmLabel>
          <h1 className="mt-3 font-display text-[clamp(2rem,4.6vw,3.2rem)] font-bold leading-[1.08] tracking-tight text-ink-high">
            Thư viện video <span className="text-gradient italic">dựng bằng Vyra</span>
          </h1>
          <p className="mt-4 text-ink-medium">
            Video thật 9:16, đủ mọi thể loại — bán hàng, KOL ảo, thể loại, ảnh sản phẩm. Rê chuột để
            xem clip chạy. Thấy kiểu nào ưng, bấm tạo cái của bạn trong 60 giây.
          </p>
        </div>

        {/* tab lọc theo nhóm việc */}
        <div className="mt-7 flex flex-wrap gap-2">
          {TABS.map((tb) => (
            <button
              key={tb}
              onClick={() => setTab(tb)}
              className={cn(
                "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors",
                tab === tb
                  ? "border-violet-400/50 bg-violet-500/15 text-violet-100"
                  : "border-white/10 bg-white/[0.03] text-ink-low hover:border-white/25 hover:text-ink-medium",
              )}
            >
              {tb}
            </button>
          ))}
        </div>

        <div className="mt-8">
          <VideoLibrary filter={tab} />
        </div>

        {/* CTA đóng trang */}
        <div className="mt-16 flex flex-col items-center gap-4 rounded-3xl glass-bordered p-10 text-center">
          <h2 className="font-display text-2xl font-bold text-ink-high sm:text-3xl">
            Muốn video như trên cho <span className="text-gradient">sản phẩm của bạn?</span>
          </h2>
          <p className="max-w-md text-ink-medium">
            Dán link hoặc tải ảnh sản phẩm, Vyra dựng thành clip bán hàng. Render lỗi không trừ tiền.
          </p>
          <Link href="/login" className="mt-1">
            <Button size="lg">Tạo video của bạn</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
