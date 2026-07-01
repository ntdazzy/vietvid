"use client";

import { useState } from "react";
import { Wand2, ChevronDown, Check, Plus } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { cn } from "@/lib/utils/cn";

// TRÌNH TÙY BIẾN SÂU (#23) — cho người KHÔNG biết viết prompt: bấm-chọn trực quan
// (số người / mặt / da / dáng / trang phục / bối cảnh / hành động / intro-CTA) → tự ghép
// thành một mô tả tiếng Việt gọn, chèn thẳng vào kịch bản. Không gọi API, không đổi backend:
// chỉ làm giàu trường brief mà wizard vốn đã gửi đi. Bộ dựng prompt phía sau lo phần còn lại.

type Grp = { key: string; label: string; multi?: boolean; opts: string[] };

const GROUPS: Grp[] = [
  { key: "people", label: "Số người", opts: ["1 người", "2 người", "Nhóm bạn", "Không có người"] },
  { key: "who", label: "Nhân vật", opts: ["Nữ trẻ", "Nam trẻ", "Mẹ bỉm", "Trẻ em", "Trung niên"] },
  { key: "skin", label: "Làn da", opts: ["Trắng hồng", "Tự nhiên", "Rám nắng khỏe"] },
  { key: "body", label: "Vóc dáng", opts: ["Mảnh mai", "Cân đối", "Đầy đặn"] },
  { key: "outfit", label: "Trang phục", opts: ["Thường ngày", "Công sở", "Dạ hội", "Thể thao", "Áo dài", "Đồng phục shop"] },
  { key: "scene", label: "Bối cảnh", opts: ["Phòng ngủ cozy", "Quán café", "Đường phố", "Studio nền sạch", "Ngoài trời", "Văn phòng"] },
  { key: "action", label: "Hành động", opts: ["Cầm & giới thiệu sản phẩm", "Nói với máy quay", "Đi bộ tới", "Xoay khoe đồ", "Nhảy theo nhạc", "Mở hộp"] },
  { key: "extra", label: "Thêm thắt", multi: true, opts: ["Có intro logo", "Chốt đơn cuối (CTA)", "Phụ đề tiếng Việt"] },
];

// Ghép các lựa chọn thành 1 câu mô tả tiếng Việt tự nhiên, bỏ nhóm chưa chọn.
function compose(sel: Record<string, string[]>): string {
  const one = (k: string) => sel[k]?.[0];
  const parts: string[] = [];
  if (one("scene")) parts.push(`Bối cảnh ${one("scene")!.toLowerCase()}`);
  const subj: string[] = [];
  if (one("people")) subj.push(one("people")!.toLowerCase());
  if (one("who")) subj.push(one("who")!.toLowerCase());
  const looks: string[] = [];
  if (one("skin")) looks.push(`da ${one("skin")!.toLowerCase()}`);
  if (one("body")) looks.push(`dáng ${one("body")!.toLowerCase()}`);
  if (one("outfit")) looks.push(`mặc đồ ${one("outfit")!.toLowerCase()}`);
  let sentence = subj.join(" ");
  if (looks.length) sentence += (sentence ? ", " : "") + looks.join(", ");
  if (one("action")) sentence += (sentence ? ", " : "") + one("action")!.toLowerCase();
  if (sentence) parts.push(sentence);
  const extra = sel["extra"] || [];
  const tail: string[] = [];
  if (extra.includes("Có intro logo")) tail.push("mở đầu có intro logo");
  if (extra.includes("Chốt đơn cuối (CTA)")) tail.push("kết bằng lời kêu gọi chốt đơn");
  if (extra.includes("Phụ đề tiếng Việt")) tail.push("có phụ đề tiếng Việt");
  if (tail.length) parts.push(tail.join(", "));
  return parts.join(". ") + (parts.length ? "." : "");
}

export function SceneBuilder() {
  const w = useWizard();
  const [open, setOpen] = useState(false);
  const [sel, setSel] = useState<Record<string, string[]>>({});

  function toggle(g: Grp, opt: string) {
    setSel((s) => {
      const cur = s[g.key] || [];
      if (g.multi) {
        return { ...s, [g.key]: cur.includes(opt) ? cur.filter((x) => x !== opt) : [...cur, opt] };
      }
      return { ...s, [g.key]: cur[0] === opt ? [] : [opt] };
    });
  }

  const preview = compose(sel);
  const hasAny = Object.values(sel).some((v) => v.length > 0);

  function apply() {
    if (!preview) return;
    const existing = w.brief.trim();
    w.patch({ brief: existing ? `${existing}\n${preview}` : preview });
  }

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02]">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2.5 px-4 py-3 text-left"
      >
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-violet-400/20 bg-violet-500/10 text-violet-300">
          <Wand2 className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-ink-high">Trình tùy biến (không cần biết viết prompt)</span>
          <span className="block text-[11px] text-ink-low">Bấm-chọn người, da, dáng, trang phục, bối cảnh, hành động → tự ghép mô tả</span>
        </span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-ink-low transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] p-4">
          {GROUPS.map((g) => (
            <div key={g.key}>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-low">{g.label}</div>
              <div className="flex flex-wrap gap-1.5">
                {g.opts.map((opt) => {
                  const active = (sel[g.key] || []).includes(opt);
                  return (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => toggle(g, opt)}
                      className={cn(
                        "inline-flex items-center gap-1 rounded-lg border px-2.5 py-1 text-xs transition-colors",
                        active
                          ? "border-violet-500/60 bg-violet-500/15 text-violet-100"
                          : "border-white/10 text-ink-medium hover:border-white/25",
                      )}
                    >
                      {active && <Check className="h-3 w-3" />}
                      {opt}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* preview mô tả ghép + nút áp */}
          <div className="rounded-xl border border-white/[0.06] bg-bg-base/40 p-3">
            <div className="text-[11px] uppercase tracking-wider text-ink-low">Mô tả tự ghép</div>
            <p className="mt-1 min-h-[2.2em] text-sm text-ink-medium">
              {preview || <span className="text-ink-low">Chọn vài mục ở trên để xem mô tả…</span>}
            </p>
            <button
              type="button"
              onClick={apply}
              disabled={!hasAny}
              className={cn(
                "mt-2.5 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
                hasAny
                  ? "bg-grad-brand text-white shadow-glow-sm active:scale-95"
                  : "cursor-not-allowed bg-white/[0.04] text-ink-low",
              )}
            >
              <Plus className="h-3.5 w-3.5" /> Áp vào kịch bản
            </button>
          </div>

          <p className="text-[11px] leading-snug text-ink-low">
            Mẹo: muốn giữ đúng gương mặt / sản phẩm thật? Tải ảnh ở bước <span className="text-ink-medium">Nguồn</span> hoặc
            khoá gương mặt ở mục <span className="text-ink-medium">KOL / Nhân vật</span> — mô tả này sẽ bám theo.
          </p>
        </div>
      )}
    </div>
  );
}
