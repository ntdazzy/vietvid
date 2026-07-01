"use client";

import { useState } from "react";
import Link from "next/link";
import { BarChart3, Sparkles, TrendingUp, ArrowRight, Trophy } from "lucide-react";
import { StudioShell } from "@/components/studio/studio-shell";
import { cn } from "@/lib/utils/cn";

// PHÂN TÍCH ĐƠN (#17) — client-side thật: người bán DÁN dữ liệu đơn (tên SP + số lượng, có thể
// kèm doanh thu) copy từ Shopee/TikTok Shop → tự bóc tên + số, gộp trùng, xếp hạng SP bán chạy,
// gợi ý GÓC video cho từng SP, và bấm tạo video luôn. Không gọi API, không đổi backend.

type Row = { name: string; qty: number; revenue: number };

function fmt(n: number) {
  return n.toLocaleString("vi-VN");
}

// Bóc mỗi dòng: bỏ ký hiệu tiền, lấy các cụm số; tên = phần chữ còn lại.
function parse(text: string): Row[] {
  const agg = new Map<string, { qty: number; revenue: number }>();
  for (const raw of text.split(/\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const clean = line.replace(/₫|VNĐ|VND|đồng/gi, " ").replace(/\bđ\b/gi, " ");
    const nums = (clean.match(/\d[\d.,]*/g) || [])
      .map((s) => parseInt(s.replace(/[.,\s]/g, ""), 10))
      .filter((n) => Number.isFinite(n) && n > 0);
    const name = clean.replace(/\d[\d.,]*/g, " ").replace(/[|,;\t]+/g, " ").replace(/\s+/g, " ").trim();
    if (!name || nums.length === 0) continue;
    let qty = nums[0];
    let revenue = 0;
    if (nums.length >= 2) {
      const sorted = [...nums].sort((a, b) => a - b);
      qty = sorted[0];
      revenue = sorted[sorted.length - 1];
    }
    const cur = agg.get(name) || { qty: 0, revenue: 0 };
    agg.set(name, { qty: cur.qty + qty, revenue: cur.revenue + revenue });
  }
  return [...agg.entries()].map(([name, v]) => ({ name, ...v }));
}

const ANGLES = [
  { tag: "Best-seller", angle: "Khoe 'bán chạy nhất shop' + tạo FOMO sắp hết hàng." },
  { tag: "Á quân", angle: "Video lý do nên mua / so sánh với hàng thường." },
  { tag: "Top 3", angle: "Review chi tiết, cận cảnh chất liệu, chốt đơn." },
  { tag: "Đang lên", angle: "Thử 1 hook mạnh 3 giây xem có bật thêm không." },
];

const SAMPLE = `Áo thun oversize trắng\t142\t35.500.000
Quần jean ống rộng\t98\t44.100.000
Áo khoác dù local brand\t76\t53.200.000
Túi tote canvas\t64\t9.600.000
Giày sneaker trắng\t41\t28.700.000
Nón bucket\t120\t7.200.000`;

export default function OrderAnalysisPage() {
  const [text, setText] = useState("");
  const [rows, setRows] = useState<Row[] | null>(null);

  const hasRevenue = rows?.some((r) => r.revenue > 0) ?? false;
  const sorted = rows
    ? [...rows].sort((a, b) => (hasRevenue ? b.revenue - a.revenue : b.qty - a.qty))
    : [];
  const maxVal = sorted.length ? (hasRevenue ? sorted[0].revenue : sorted[0].qty) : 1;
  const totalQty = sorted.reduce((s, r) => s + r.qty, 0);
  const totalRev = sorted.reduce((s, r) => s + r.revenue, 0);

  function analyze(src?: string) {
    const input = src ?? text;
    setText(input);
    setRows(parse(input));
  }

  return (
    <StudioShell>
      <div className="flex flex-col gap-6 pb-24">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-violet-300">
            <BarChart3 className="h-3.5 w-3.5" /> Phân tích đơn
          </div>
          <h1 className="mt-3 font-display text-2xl font-bold text-ink-high sm:text-3xl">
            Tìm sản phẩm <span className="text-gradient">đáng làm video</span>
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-ink-medium">
            Dán dữ liệu đơn từ Shopee / TikTok Shop (tên sản phẩm + số lượng bán, kèm doanh thu nếu có).
            Vyra xếp hạng hàng bán chạy và gợi ý góc video nên làm trước — đỡ phải đoán.
          </p>
        </div>

        {/* nhập liệu */}
        <div className="rounded-2xl glass-bordered p-4">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={"Dán mỗi sản phẩm một dòng, ví dụ:\nÁo thun trắng   35   8.750.000\nQuần jean   20"}
            className="min-h-[150px] w-full resize-y rounded-xl border border-white/10 bg-bg-base/50 px-3.5 py-3 text-sm text-ink-high outline-none placeholder:text-ink-low focus:border-violet-500/40"
          />
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => analyze()}
              disabled={!text.trim()}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold transition",
                text.trim() ? "bg-grad-brand text-white shadow-glow-sm active:scale-95" : "cursor-not-allowed bg-white/[0.04] text-ink-low",
              )}
            >
              <Sparkles className="h-4 w-4" /> Phân tích
            </button>
            <button
              onClick={() => analyze(SAMPLE)}
              className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-ink-medium transition hover:border-violet-400/30 hover:text-ink-high"
            >
              Dùng dữ liệu mẫu
            </button>
            {rows && (
              <span className="ml-auto text-xs text-ink-low">
                {sorted.length} sản phẩm · {fmt(totalQty)} đơn{totalRev > 0 ? ` · ${fmt(totalRev)}₫` : ""}
              </span>
            )}
          </div>
        </div>

        {/* kết quả */}
        {rows && sorted.length === 0 && (
          <p className="text-sm text-ink-low">Chưa bóc được dòng nào. Mỗi dòng cần có tên sản phẩm + ít nhất một con số (số lượng).</p>
        )}
        {sorted.length > 0 && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-ink-high">
              <TrendingUp className="h-4 w-4 text-violet-300" /> Xếp hạng {hasRevenue ? "theo doanh thu" : "theo số đơn"}
            </div>
            {sorted.map((r, i) => {
              const val = hasRevenue ? r.revenue : r.qty;
              const pct = Math.max(4, Math.round((val / maxVal) * 100));
              const a = ANGLES[Math.min(i, ANGLES.length - 1)];
              return (
                <div key={r.name} className="rounded-2xl glass-bordered p-4">
                  <div className="flex items-start gap-3">
                    <span
                      className={cn(
                        "grid h-9 w-9 shrink-0 place-items-center rounded-xl text-sm font-bold",
                        i === 0 ? "bg-amber-500/15 text-amber-300" : "bg-white/[0.05] text-ink-medium",
                      )}
                    >
                      {i === 0 ? <Trophy className="h-4 w-4" /> : i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="truncate font-display text-sm font-semibold text-ink-high">{r.name}</span>
                        <span className="shrink-0 text-xs text-ink-low">
                          {fmt(r.qty)} đơn{r.revenue > 0 ? ` · ${fmt(r.revenue)}₫` : ""}
                        </span>
                      </div>
                      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                        <div className="h-full rounded-full bg-grad-brand" style={{ width: `${pct}%` }} />
                      </div>
                      <div className="mt-2.5 flex flex-wrap items-center gap-2">
                        <span className="rounded-md bg-violet-500/10 px-2 py-0.5 text-[11px] font-semibold text-violet-200">{a.tag}</span>
                        <span className="text-xs text-ink-medium">{a.angle}</span>
                      </div>
                    </div>
                    <Link
                      href="/app/create?feature=product_ad"
                      className="hidden shrink-0 items-center gap-1 self-center rounded-lg border border-violet-400/30 px-3 py-1.5 text-xs font-semibold text-violet-200 transition hover:bg-violet-500/10 sm:inline-flex"
                    >
                      Tạo video <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                  <Link
                    href="/app/create?feature=product_ad"
                    className="mt-3 inline-flex items-center gap-1 rounded-lg border border-violet-400/30 px-3 py-1.5 text-xs font-semibold text-violet-200 transition hover:bg-violet-500/10 sm:hidden"
                  >
                    Tạo video cho SP này <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              );
            })}
            <p className="text-[11px] text-ink-low">
              Gợi ý: làm video cho Top 3 trước — đó là hàng thị trường đã chứng minh có nhu cầu, tỉ lệ ra đơn cao hơn thử hàng mới.
            </p>
          </div>
        )}
      </div>
    </StudioShell>
  );
}
