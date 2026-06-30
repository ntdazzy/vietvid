import { Reveal } from "@/components/marketing/reveal";

// Thay "đám đông 50.000 creator" của autovis bằng SỐ NĂNG LỰC THẬT (Vyra mới, không bịa traction).
// pinned marketing copy — giữ đồng bộ với app_api/voices.py (7 giọng) + free-grant default (300 credit).
const STATS = [
  { n: "~60s", l: "mỗi video, từ 1 ảnh", ctx: "render pipeline" },
  { n: "7", l: "giọng Việt thật", ctx: "Mai · Linh · Trang · Bống · Khoa · Hùng · Tú" },
  { n: "300", l: "credit tặng, không cần thẻ", ctx: "đủ làm video đầu tiên" },
  { n: "3", l: "tỉ lệ xuất một lần dựng", ctx: "9:16 · 1:1 · 16:9" },
];

export function ProofStrip() {
  return (
    <section className="mx-auto max-w-[1280px] px-4 py-16 lg:py-20">
      <Reveal>
        <p className="mb-4 text-center text-xs font-semibold uppercase tracking-[0.18em] text-violet-300">
          Năng lực sản phẩm
        </p>
        {/* 1 khối số liền (không 4 card kính rời) + divider dọc */}
        <div className="grid grid-cols-2 overflow-hidden rounded-[24px] glass-bordered lg:grid-cols-4 lg:divide-x lg:divide-white/[0.06]">
          {STATS.map((s) => (
            <div key={s.l} className="p-6 text-center">
              <div className="font-numeric text-[clamp(2rem,4vw,2.75rem)] font-bold leading-none text-gradient">
                {s.n}
              </div>
              <div className="mt-2 text-sm text-ink-medium">{s.l}</div>
              <div className="mt-1 text-[11px] text-ink-disabled">{s.ctx}</div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-ink-low">
          Tất cả số trên là năng lực sản phẩm, không phải số người dùng. Vyra mới ra mắt — không có
          &ldquo;50.000 creator&rdquo; để khoe.
        </p>
      </Reveal>
    </section>
  );
}
