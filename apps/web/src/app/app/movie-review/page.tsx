"use client";

import { useState } from "react";
import Link from "next/link";
import { Clapperboard, Sparkles, Copy, Check, Mic2, ArrowRight } from "lucide-react";
import { StudioShell } from "@/components/studio/studio-shell";
import { cn } from "@/lib/utils/cn";

// REVIEW PHIM (#20) — bản tạo DÀN Ý client-side thật (không cần API): nhập tên phim + tông + độ dài
// → ghép kịch bản review theo cấu trúc viral (hook → giới thiệu → điểm hay → điểm chưa tới → chấm
// điểm → chốt), sửa được từng đoạn, rồi bấm đọc giọng Việt / dựng video. "Auto" đầy đủ (LLM viết
// nội dung phim cụ thể) là tầng có API — nút wire sẵn sang /app/audio + /app/create.

type Tone = "khen" | "canbang" | "che" | "tomtat";
const TONES: { id: Tone; label: string; note: string }[] = [
  { id: "khen", label: "Khen nồng nhiệt", note: "phải xem ngay" },
  { id: "canbang", label: "Cân bằng", note: "khách quan hay–dở" },
  { id: "che", label: "Chê thẳng", note: "tiết kiệm tiền vé" },
  { id: "tomtat", label: "Tóm tắt không spoiler", note: "gợi tò mò" },
];
const LENGTHS = [
  { s: 30, label: "30 giây", n: "hook + 1 ý" },
  { s: 60, label: "60 giây", n: "đủ khen–chê" },
  { s: 90, label: "90 giây", n: "review sâu" },
];

function build(movie: string, tone: Tone, secs: number): { h: string; body: string }[] {
  const m = movie.trim() || "bộ phim này";
  const hooks: Record<Tone, string> = {
    khen: `Đừng lướt — "${m}" là phim khiến mình phải viết review ngay khi vừa ra rạp.`,
    canbang: `"${m}" đang gây tranh cãi. Xem hay không, coi hết 30 giây này rồi quyết.`,
    che: `Mình vừa mất tiền vé xem "${m}" để bạn không phải mất. Nghe mình nói.`,
    tomtat: `"${m}" nói về điều gì mà ai cũng nhắc? Không spoiler, mình kể nhanh.`,
  };
  const verdicts: Record<Tone, string> = {
    khen: `Chấm 9/10. Đáng đồng tiền, nên xem ở rạp để đã tai đã mắt.`,
    canbang: `Chấm 7/10. Hay có, dở có — hợp gu ai thích thể loại này.`,
    che: `Chấm 4/10. Chờ lên nền tảng xem cho đỡ phí, đừng ra rạp.`,
    tomtat: `Xem để tự chấm — nhưng phần mở đầu đủ giữ bạn tới cuối.`,
  };
  const secen: { h: string; body: string }[] = [
    { h: "Hook (3 giây đầu)", body: hooks[tone] },
    { h: "Giới thiệu nhanh", body: `Thể loại, ai đạo diễn, ai đóng chính của "${m}" — nói gọn 1 câu, không dài dòng.` },
    { h: "Điểm hay nhất", body: `Nêu 1 thứ khiến "${m}" đáng nhớ: hình ảnh, diễn xuất, hay cái twist. Kể cảm giác, đừng kể cốt truyện.` },
  ];
  if (secs >= 60) {
    secen.push({ h: "Điểm hay #2", body: `Thêm 1 điểm cộng nữa (âm nhạc / nhịp phim / thông điệp) để review có sức nặng.` });
    secen.push({ h: "Điểm chưa tới", body: tone === "khen" ? `Một nhược điểm nhỏ cho khách quan (hơi dài, vài đoạn chậm).` : `Nói thẳng chỗ dở của "${m}" khiến bạn tiếc.` });
  }
  if (secs >= 90) {
    secen.push({ h: "Dành cho ai", body: `"${m}" hợp người thích gì, không hợp ai — giúp người xem tự soi mình.` });
  }
  secen.push({ h: "Chấm điểm", body: verdicts[tone] });
  secen.push({ h: "Chốt / CTA", body: `Câu chốt + kêu gọi: "Bạn xem chưa? Bình luận cho mình biết", theo dõi để xem review phim mỗi tuần.` });
  return secen;
}

export default function MovieReviewPage() {
  const [movie, setMovie] = useState("");
  const [tone, setTone] = useState<Tone>("canbang");
  const [secs, setSecs] = useState(60);
  const [script, setScript] = useState<{ h: string; body: string }[] | null>(null);
  const [copied, setCopied] = useState(false);

  function gen() {
    setScript(build(movie, tone, secs));
  }
  const full = script ? script.map((s) => s.body).join("\n\n") : "";
  function copy() {
    navigator.clipboard?.writeText(full).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }).catch(() => {});
  }

  return (
    <StudioShell>
      <div className="flex flex-col gap-6 pb-24">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-violet-300">
            <Clapperboard className="h-3.5 w-3.5" /> Review phim
          </div>
          <h1 className="mt-3 font-display text-2xl font-bold text-ink-high sm:text-3xl">
            Kịch bản review phim <span className="text-gradient">sẵn để đọc</span>
          </h1>
          <p className="mt-2 max-w-2xl text-sm text-ink-medium">
            Nhập tên phim, chọn tông và độ dài — Vyra dựng dàn ý review theo cấu trúc dễ viral (hook → điểm
            hay → chấm điểm → chốt). Sửa lời cho hợp bạn, rồi đọc bằng giọng Việt hoặc dựng thành video.
          </p>
        </div>

        <div className="rounded-2xl glass-bordered p-4">
          <input
            value={movie}
            onChange={(e) => setMovie(e.target.value)}
            placeholder="Tên phim (vd: Mai, Đào Phở và Piano, Dune 2…)"
            className="w-full rounded-xl border border-white/10 bg-bg-base/50 px-3.5 py-2.5 text-sm text-ink-high outline-none placeholder:text-ink-low focus:border-violet-500/40"
          />
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-low">Tông review</div>
              <div className="flex flex-wrap gap-1.5">
                {TONES.map((tt) => (
                  <button
                    key={tt.id}
                    onClick={() => setTone(tt.id)}
                    className={cn(
                      "rounded-lg border px-2.5 py-1 text-xs transition-colors",
                      tone === tt.id ? "border-violet-500/60 bg-violet-500/15 text-violet-100" : "border-white/10 text-ink-medium hover:border-white/25",
                    )}
                  >
                    {tt.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-ink-low">Độ dài</div>
              <div className="grid grid-cols-3 gap-2">
                {LENGTHS.map((l) => (
                  <button
                    key={l.s}
                    onClick={() => setSecs(l.s)}
                    className={cn(
                      "flex flex-col items-center gap-0.5 rounded-xl border py-2 transition-colors",
                      secs === l.s ? "border-violet-500/60 bg-violet-500/10" : "border-white/10 hover:border-white/25",
                    )}
                  >
                    <span className={cn("text-sm font-semibold", secs === l.s ? "text-ink-high" : "text-ink-medium")}>{l.label}</span>
                    <span className="text-[10px] text-ink-low">{l.n}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
          <button
            onClick={gen}
            className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-grad-brand px-4 py-2 text-sm font-semibold text-white shadow-glow-sm transition active:scale-95"
          >
            <Sparkles className="h-4 w-4" /> Tạo dàn ý review
          </button>
        </div>

        {script && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-ink-high">Dàn ý review · {secs}s</span>
              <button onClick={copy} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-ink-medium transition hover:border-violet-400/30 hover:text-ink-high">
                {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? "Đã chép" : "Chép kịch bản"}
              </button>
            </div>
            {script.map((s, i) => (
              <div key={i} className="rounded-2xl glass-bordered p-4">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-violet-300/80">{s.h}</div>
                <p className="mt-1.5 text-sm leading-relaxed text-ink-medium">{s.body}</p>
              </div>
            ))}
            <div className="flex flex-wrap gap-2 pt-1">
              <Link href="/app/audio" className="inline-flex items-center gap-1.5 rounded-xl bg-grad-brand px-4 py-2 text-sm font-semibold text-white shadow-glow-sm transition active:scale-95">
                <Mic2 className="h-4 w-4" /> Đọc bằng giọng Việt
              </Link>
              <Link href="/app/create?feature=text_to_video" className="inline-flex items-center gap-1.5 rounded-xl border border-violet-400/30 px-4 py-2 text-sm font-semibold text-violet-200 transition hover:bg-violet-500/10">
                Dựng thành video <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <p className="text-[11px] text-ink-low">
              Đây là dàn ý theo cấu trúc — thay lời cho hợp giọng bạn. Giọng đọc tiếng Việt (đọc số, tên nước
              ngoài, cảm xúc) làm ở bước Âm thanh; nhân bản giọng riêng là tính năng đang mở dần.
            </p>
          </div>
        )}
      </div>
    </StudioShell>
  );
}
