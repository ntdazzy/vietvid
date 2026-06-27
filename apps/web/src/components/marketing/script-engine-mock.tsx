"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

// 6 góc THẬT (scriptgen.py ANGLE_LABELS) + beat mẫu theo template thật. MOCK client-side.
type Beat = { t: string; label: string; text: string };
type Angle = { key: string; label: string; beats: Beat[] };

const ANGLES: Angle[] = [
  { key: "ps", label: "Vấn đề → Giải pháp", beats: [
    { t: "00:00", label: "Hook", text: "Cái này giải quyết gọn vụ bạn đang đau đầu." },
    { t: "00:05", label: "Nỗi đau", text: "Trước mình vật vã với nó miết, bực dễ sợ." },
    { t: "00:12", label: "Lợi ích", text: "Có rồi là nhẹ hẳn, tiện gấp mấy lần." },
    { t: "00:20", label: "Chốt", text: "Để link giỏ hàng rồi, bấm vô lẹ nha!" },
  ]},
  { key: "sp", label: "Đám đông tin dùng", beats: [
    { t: "00:00", label: "Hook", text: "Cả nhà rủ nhau mua, mình cũng phải thử." },
    { t: "00:06", label: "Lợi ích", text: "Xài rồi mới hiểu vì sao nó hot tới vậy." },
    { t: "00:13", label: "Khao khát", text: "Giờ tới lượt mình nghiện, mua là không hối." },
    { t: "00:21", label: "Chốt", text: "Chốt cùng hội luôn cho nóng nha!" },
  ]},
  { key: "tf", label: "Lột xác trước → sau", beats: [
    { t: "00:00", label: "Hook", text: "Trước với sau — khác một trời một vực!" },
    { t: "00:05", label: "Nỗi đau", text: "Hồi trước nhìn chán, tự ti dễ sợ." },
    { t: "00:12", label: "Lợi ích", text: "Có vô phát là lên đời, tự tin hẳn." },
    { t: "00:20", label: "Chốt", text: "Muốn lột xác như mình thì bấm giỏ hàng!" },
  ]},
  { key: "fomo", label: "Sợ bỏ lỡ / sắp hết", beats: [
    { t: "00:00", label: "Hook", text: "Sắp hết hàng rồi, nhanh tay kẻo tiếc!" },
    { t: "00:06", label: "Lợi ích", text: "Đợt này deal hời, qua đợt là về giá gốc." },
    { t: "00:13", label: "Khao khát", text: "Mình canh mãi mới hốt được, sướng gì đâu." },
    { t: "00:21", label: "Chốt", text: "Còn hàng là còn cơ hội, chốt liền!" },
  ]},
  { key: "cmp", label: "So sánh hơn hẳn", beats: [
    { t: "00:00", label: "Hook", text: "Thử cái này xong là khỏi quay lại loại cũ!" },
    { t: "00:05", label: "Nỗi đau", text: "Loại rẻ tiền dùng bực, mau hư thấy ghê." },
    { t: "00:12", label: "Lợi ích", text: "Cái này mượt, bền, đáng từng đồng." },
    { t: "00:20", label: "Chốt", text: "Có nhiêu mà nâng cấp hẳn, bấm đi nha!" },
  ]},
  { key: "cur", label: "Tò mò khó cưỡng", beats: [
    { t: "00:00", label: "Hook", text: "Cái này làm được điều bạn không ngờ tới đâu." },
    { t: "00:06", label: "Lợi ích", text: "Nhìn vậy thôi chứ công dụng bất ngờ cực." },
    { t: "00:13", label: "Khao khát", text: "Coi xong là hiểu vì sao mình mê tít." },
    { t: "00:21", label: "Chốt", text: "Tò mò thì thử đi, link giỏ hàng nha!" },
  ]},
];

export function ScriptEngineMock() {
  const reduce = useReducedMotion();
  const [active, setActive] = useState(ANGLES[0]);
  return (
    <div className="glass-bordered rounded-[24px] p-5">
      <div className="flex flex-wrap gap-1.5">
        {ANGLES.map((a) => (
          <button
            key={a.key}
            onClick={() => setActive(a)}
            className={cn(
              "rounded-lg border px-2.5 py-1 text-xs transition-colors",
              active.key === a.key
                ? "border-violet-500/60 bg-violet-500/15 text-violet-100"
                : "border-white/10 text-ink-low hover:border-white/25",
            )}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="mt-4 min-h-[188px] rounded-2xl border border-white/[0.06] bg-bg-base/40 p-4">
        <AnimatePresence mode="wait">
          <motion.ul
            key={active.key}
            initial={{ opacity: 0, y: reduce ? 0 : 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: reduce ? 0 : -8 }}
            transition={{ duration: 0.28 }}
            className="flex flex-col gap-2"
          >
            {active.beats.map((b, i) => (
              <li key={b.t} className="flex gap-2.5 text-sm">
                <span className="shrink-0 font-numeric text-[11px] text-ink-low">{b.t}</span>
                <span className="w-16 shrink-0 text-[11px] font-semibold uppercase tracking-wide text-violet-300/80">
                  {b.label}
                </span>
                <span className="text-ink-medium">
                  {b.text}
                  {i === active.beats.length - 1 && <span className="caret-blink ml-0.5 text-violet-300">▍</span>}
                </span>
              </li>
            ))}
          </motion.ul>
        </AnimatePresence>
      </div>
    </div>
  );
}
