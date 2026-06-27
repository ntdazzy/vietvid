"use client";

import { motion } from "framer-motion";
import { Link2, Check, Webhook } from "lucide-react";
import { Reveal } from "@/components/marketing/reveal";

// Endpoint THẬT: dán link = POST /v1/products/import; B2B = POST /api/v1/videos + X-API-Key.
const PREFILL = ["Tên SP", "Giá", "Ảnh"];

export function IntegrationBand() {
  return (
    <div className="glass-bordered grid overflow-hidden rounded-[24px] lg:grid-cols-2">
      {/* dán link sàn */}
      <Reveal className="p-6 lg:p-8">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-violet-300">
          <Link2 className="h-3.5 w-3.5" /> Dán link sàn
        </div>
        <h3 className="mt-3 font-display text-xl font-bold text-ink-high">
          Dán một đường link. Phần còn lại tự điền.
        </h3>
        <div className="mt-4 flex items-center rounded-xl border border-white/10 bg-bg-base/50 px-3 py-2.5">
          <span className="truncate font-numeric text-sm text-ink-medium">https://shopee.vn/…</span>
          <span className="caret-blink ml-0.5 text-violet-300">▍</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {PREFILL.map((p, i) => (
            <motion.span
              key={p}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 + 0.12 * i }}
              className="inline-flex items-center gap-1 rounded-lg border border-success/30 bg-success/[0.07] px-2 py-1 text-xs text-success"
            >
              <Check className="h-3 w-3" /> {p}
            </motion.span>
          ))}
        </div>
        <p className="mt-3 text-xs text-ink-low">Hỗ trợ Shopee · TikTok Shop · Lazada.</p>
      </Reveal>

      {/* API B2B */}
      <Reveal delay={0.1} className="border-t border-white/[0.06] p-6 lg:border-l lg:border-t-0 lg:p-8">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-violet-300">
          <Webhook className="h-3.5 w-3.5" /> API B2B · webhook
        </div>
        <h3 className="mt-3 font-display text-xl font-bold text-ink-high">
          Tạo video bằng code. Nhận webhook khi xong.
        </h3>
        <pre className="mt-4 overflow-x-auto rounded-xl bg-bg-base/60 p-4 font-mono text-xs leading-relaxed text-ink-medium">
{`POST /api/v1/videos
X-API-Key: vv_live_••••

{
  "product": { "name": "Tai nghe ABC" },
  "voice_persona": "mai",
  "aspect": "9:16"
}`}
        </pre>
        <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-ink-low">
          <Webhook className="h-3 w-3 text-violet-300" /> Bắn sự kiện <span className="font-numeric text-ink-medium">video.ready</span> khi render xong.
        </p>
      </Reveal>
    </div>
  );
}
