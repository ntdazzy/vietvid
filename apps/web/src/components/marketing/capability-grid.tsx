"use client";

import { CapabilityCard } from "@/components/marketing/capability-card";
import { Reveal } from "@/components/marketing/reveal";
import { MiniReel } from "@/components/marketing/mini-reel";
import { VariantLeaderboard } from "@/components/marketing/winner-loop";
import { VoiceRail } from "@/components/marketing/voice-rail";
import { ScriptEngineMock } from "@/components/marketing/script-engine-mock";
import { RatioBento } from "@/components/marketing/ratio-bento";
import { IntegrationBand } from "@/components/marketing/integration-band";

// Khối đấu trực diện autovis: 6 năng lực đánh số 01–06, MỖI ô là demo SỐNG (không ảnh ghép tĩnh).
// Demo nặng (02 leaderboard, 06 API) thu nhỏ + khoá tương tác trong lưới (deep-dive đầy đủ ở act dưới).
export function CapabilityGrid() {
  const cards = [
    {
      index: 1, tone: "core" as const, badge: "Lõi", title: "Ảnh → Video 60s", href: "/login",
      desc: "Thả 1 ảnh, Vyra dựng video 60 giây có nhịp, có chốt đơn.",
      demo: <MiniReel poster="/samples/fashion.jpg" className="mx-auto h-full max-h-[230px] w-auto"
        captions={["Mới săn được em này nè…", "Mặc lên tôn dáng ghê!", "Để giỏ hàng rồi nha!"]} />,
    },
    {
      index: 2, tone: "moat" as const, badge: "Độc quyền", title: "Đo click → bản thắng", href: "#winner-loop",
      desc: "Tạo nhiều biến thể, đo click thật, xếp hạng, giữ bản bán được. Đối thủ Việt không có.",
      demo: (
        <div className="pointer-events-none origin-top scale-[0.82] sm:scale-90">
          <VariantLeaderboard />
        </div>
      ),
    },
    {
      index: 3, tone: "hot" as const, badge: "Hot", title: "7 giọng Việt", href: "/login",
      desc: "Mai, Linh, Trang, Bống, Khoa, Hùng, Tú — 7 chất giọng thật.",
      demo: <div className="max-h-[240px] overflow-hidden"><VoiceRail /></div>,
    },
    {
      index: 4, tone: "new" as const, badge: "Mới", title: "Kịch bản 6 góc", href: "/login",
      desc: "Sáu góc chốt đơn theo timecode, sửa từng câu.",
      demo: <ScriptEngineMock />,
    },
    {
      index: 5, tone: "new" as const, badge: "Mới", title: "Đa tỉ lệ", href: "/login",
      desc: "Một lần dựng, xuất 9:16 · 1:1 · 16:9.",
      demo: <RatioBento />,
    },
    {
      index: 6, tone: "new" as const, badge: "API", title: "Dán link + API", href: "/login",
      desc: "Dán link sàn tự bóc ảnh/tên/giá; có API + webhook B2B.",
      demo: (
        <div className="pointer-events-none origin-top scale-[0.8] sm:scale-[0.85]">
          <IntegrationBand />
        </div>
      ),
    },
  ];

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {cards.map((c, i) => (
        <Reveal key={c.index} delay={0.06 * i}>
          <CapabilityCard index={c.index} tone={c.tone} badge={c.badge} title={c.title} desc={c.desc} href={c.href}>
            {c.demo}
          </CapabilityCard>
        </Reveal>
      ))}
    </div>
  );
}
