"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

// 6 góc THẬT (scriptgen.py ANGLE_LABELS) — mỗi beat có timecode + lời thoại + CHỈ ĐẠO CẢNH
// (shot/visual) như kịch bản dựng thật, không chỉ 1 dòng chung. MOCK client-side.
type Beat = { t: string; label: string; text: string; scene: string };
type Angle = { key: string; label: string; beats: Beat[] };

const ANGLES: Angle[] = [
  { key: "ps", label: "Vấn đề → Giải pháp", beats: [
    { t: "00:00", label: "Hook", text: "Cái này giải quyết gọn vụ bạn đang đau đầu.", scene: "Cận mặt KOL nhìn thẳng máy quay, ánh sáng ấm" },
    { t: "00:05", label: "Nỗi đau", text: "Trước mình vật vã với nó miết, bực dễ sợ.", scene: "B-roll cảnh dùng đồ cũ lỗi, nhịp cắt nhanh" },
    { t: "00:12", label: "Giải pháp", text: "Tới hồi gặp em này, thử liều một phen.", scene: "Mở hộp sản phẩm, cận tay cầm, light sweep" },
    { t: "00:20", label: "Lợi ích", text: "Có rồi là nhẹ hẳn, tiện gấp mấy lần.", scene: "Split-screen trước/sau, demo công dụng" },
    { t: "00:28", label: "Bằng chứng", text: "Xài tuần rồi, ưng không tả nổi luôn.", scene: "KOL reaction cười, overlay đánh giá 5 sao" },
    { t: "00:34", label: "Chốt", text: "Để link giỏ hàng rồi, bấm vô lẹ nha!", scene: "Cận sản phẩm + nút giỏ hàng nhấp nháy" },
  ]},
  { key: "sp", label: "Đám đông tin dùng", beats: [
    { t: "00:00", label: "Hook", text: "Cả nhà rủ nhau mua, mình cũng phải thử.", scene: "Cảnh đông người dùng, montage nhanh" },
    { t: "00:06", label: "Tò mò", text: "Hot tới vậy chắc phải có lý do gì đó.", scene: "KOL nghiêng đầu, biểu cảm tò mò" },
    { t: "00:13", label: "Lợi ích", text: "Xài rồi mới hiểu vì sao nó cháy hàng.", scene: "Demo cận cảnh, text overlay điểm cộng" },
    { t: "00:21", label: "Khao khát", text: "Giờ tới lượt mình nghiện, mua là không hối.", scene: "KOL ôm sản phẩm, ánh sáng vàng ấm" },
    { t: "00:29", label: "Chốt", text: "Chốt cùng hội luôn cho nóng nha!", scene: "Nút mua + đếm số người đang xem" },
  ]},
  { key: "tf", label: "Lột xác trước → sau", beats: [
    { t: "00:00", label: "Hook", text: "Trước với sau — khác một trời một vực!", scene: "Cú lia chuyển cảnh trước/sau gây sốc" },
    { t: "00:06", label: "Nỗi đau", text: "Hồi trước nhìn chán, tự ti dễ sợ.", scene: "Tông xám lạnh, cảnh 'trước' kém sắc" },
    { t: "00:13", label: "Bước ngoặt", text: "Tình cờ thử em này một lần cho biết.", scene: "Khoảnh khắc dùng sản phẩm, slow-mo" },
    { t: "00:21", label: "Lợi ích", text: "Có vô phát là lên đời, tự tin hẳn.", scene: "Tông ấm rực, cảnh 'sau' bừng sáng" },
    { t: "00:29", label: "Chốt", text: "Muốn lột xác như mình thì bấm giỏ hàng!", scene: "CTA + before/after thu nhỏ góc màn" },
  ]},
  { key: "fomo", label: "Sợ bỏ lỡ / sắp hết", beats: [
    { t: "00:00", label: "Hook", text: "Sắp hết hàng rồi, nhanh tay kẻo tiếc!", scene: "Text 'SẮP HẾT' đỏ nhấp nháy, nhịp gấp" },
    { t: "00:06", label: "Lý do", text: "Đợt này deal hời, qua đợt là về giá gốc.", scene: "So sánh giá cũ/mới, gạch ngang giá cao" },
    { t: "00:13", label: "Bằng chứng", text: "Mình canh mãi mới hốt được, sướng gì đâu.", scene: "Cận đơn đã đặt, overlay 'còn 12 suất'" },
    { t: "00:21", label: "Khao khát", text: "Bỏ lỡ là tiếc hùi hụi cho coi.", scene: "KOL tiếc nuối rồi cười khi kịp mua" },
    { t: "00:28", label: "Chốt", text: "Còn hàng là còn cơ hội, chốt liền!", scene: "Đồng hồ đếm ngược + nút mua" },
  ]},
  { key: "cmp", label: "So sánh hơn hẳn", beats: [
    { t: "00:00", label: "Hook", text: "Thử cái này xong là khỏi quay lại loại cũ!", scene: "Đặt 2 sản phẩm cạnh nhau, cận cảnh" },
    { t: "00:06", label: "Nỗi đau", text: "Loại rẻ tiền dùng bực, mau hư thấy ghê.", scene: "B-roll loại cũ hỏng, tông xám" },
    { t: "00:13", label: "Đối chiếu", text: "Bên này mượt, bền, đáng từng đồng.", scene: "Demo song song, tick xanh vs gạch đỏ" },
    { t: "00:21", label: "Lợi ích", text: "Nâng cấp một lần, đỡ thay tới thay lui.", scene: "Cận chi tiết hoàn thiện, light sweep" },
    { t: "00:28", label: "Chốt", text: "Có nhiêu mà lên đời hẳn, bấm đi nha!", scene: "CTA + bảng so sánh thu gọn" },
  ]},
  { key: "cur", label: "Tò mò khó cưỡng", beats: [
    { t: "00:00", label: "Hook", text: "Cái này làm được điều bạn không ngờ tới đâu.", scene: "Giấu sản phẩm, chỉ hé một góc bí ẩn" },
    { t: "00:06", label: "Gợi mở", text: "Nhìn vậy thôi chứ công dụng bất ngờ cực.", scene: "Tease từng phần, chưa lộ toàn bộ" },
    { t: "00:13", label: "Tiết lộ", text: "Đây, để mình cho coi tận mắt nè.", scene: "Reveal trọn sản phẩm, cú zoom dứt khoát" },
    { t: "00:21", label: "Lợi ích", text: "Coi xong là hiểu vì sao mình mê tít.", scene: "Demo điểm wow, reaction KOL trầm trồ" },
    { t: "00:28", label: "Chốt", text: "Tò mò thì thử đi, link giỏ hàng nha!", scene: "Cận sản phẩm + CTA giỏ hàng" },
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

      <div className="mt-3 flex items-center justify-between text-[11px] text-ink-low">
        <span>Kịch bản theo timecode · lời thoại + chỉ đạo cảnh</span>
        <span className="font-numeric">~35s · {active.beats.length} cảnh</span>
      </div>

      <div className="mt-2 max-h-[300px] overflow-y-auto rounded-2xl border border-white/[0.06] bg-bg-base/40 p-4">
        <AnimatePresence mode="wait">
          <motion.ul
            key={active.key}
            initial={{ opacity: 0, y: reduce ? 0 : 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: reduce ? 0 : -8 }}
            transition={{ duration: 0.28 }}
            className="flex flex-col gap-3"
          >
            {active.beats.map((b, i) => (
              <li key={b.t} className="flex gap-2.5 text-sm">
                <span className="shrink-0 pt-0.5 font-numeric text-[11px] text-ink-low">{b.t}</span>
                <span className="w-16 shrink-0 pt-0.5 text-[11px] font-semibold uppercase tracking-wide text-violet-300/80">
                  {b.label}
                </span>
                <div className="min-w-0">
                  <p className="text-ink-medium">
                    {b.text}
                    {i === active.beats.length - 1 && <span className="caret-blink ml-0.5 text-violet-300">▍</span>}
                  </p>
                  <p className="mt-0.5 flex items-center gap-1 text-[11px] text-ink-low">
                    <span className="text-violet-300/70">▸ Cảnh:</span> {b.scene}
                  </p>
                </div>
              </li>
            ))}
          </motion.ul>
        </AnimatePresence>
      </div>
    </div>
  );
}
