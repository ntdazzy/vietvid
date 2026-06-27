"use client";

import { useRef, useState } from "react";
import { Volume2, UserSquare2, ShieldCheck, Loader2, AlertCircle } from "lucide-react";
import { useWizard } from "@/store/wizard";
import { api } from "@/lib/api/endpoints";
import { Field, ChipGroup, inputCls } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";

const SAMPLE = "Da bạn sẽ căng mướt và rạng rỡ chỉ sau bảy ngày sử dụng.";

export function VoiceStep() {
  const w = useWizard();
  const isKol = w.videoType === "kol_full";
  const [text, setText] = useState(SAMPLE);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function play() {
    setLoading(true);
    setErr(null);
    try {
      const url = await api.voicePreview(text.trim() || SAMPLE, w.voiceGender || "female");
      if (audioRef.current) {
        audioRef.current.src = url;
        await audioRef.current.play();
      }
    } catch {
      setErr("Không nghe thử được, thử lại.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-ink-high">{isKol ? "Giọng & nhân vật KOL" : "Giọng đọc"}</h2>
        <p className="mt-1 text-sm text-ink-low">
          Giọng Việt thật là điểm mạnh của VietVid. Nghe thử trước khi tạo.
        </p>
      </div>

      <Field label="Giọng">
        <ChipGroup
          value={w.voiceGender || "female"}
          onChange={(v) => w.patch({ voiceGender: v as "female" | "male" })}
          options={[
            { value: "female", label: "Nữ" },
            { value: "male", label: "Nam" },
          ]}
        />
      </Field>

      {/* nghe thử / đọc thử câu của tôi */}
      <div className="flex flex-col gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-ink-medium">
          <Volume2 className="h-4 w-4 text-violet-300" /> Đọc thử câu của bạn
        </div>
        <textarea
          className={cn(inputCls, "min-h-[64px] resize-y")}
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={200}
          placeholder="Nhập câu muốn nghe thử…"
        />
        <div className="flex items-center gap-3">
          <Button variant="glass" size="sm" onClick={play} disabled={loading} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
            {loading ? "Đang tạo giọng…" : "Nghe thử"}
          </Button>
          {err && (
            <span className="flex items-center gap-1.5 text-sm text-danger">
              <AlertCircle className="h-4 w-4" /> {err}
            </span>
          )}
        </div>
        <audio ref={audioRef} hidden />
      </div>

      {/* persona KOL — chỉ khi videoType=kol_full */}
      {isKol && (
        <div className="flex flex-col gap-4 rounded-xl border border-violet-500/25 bg-violet-500/[0.05] p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-violet-200">
            <UserSquare2 className="h-4 w-4" /> Nhân vật KOL
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Tên KOL">
              <input
                className={inputCls}
                value={w.kolName}
                onChange={(e) => w.patch({ kolName: e.target.value })}
                placeholder="Mai Anh"
              />
            </Field>
            <Field label="Phong cách">
              <input
                className={inputCls}
                value={w.kolStyle}
                onChange={(e) => w.patch({ kolStyle: e.target.value })}
                placeholder="Trẻ trung, năng động"
              />
            </Field>
          </div>

          <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-white/10 bg-white/[0.02] p-3">
            <input
              type="checkbox"
              checked={w.consent}
              onChange={(e) => w.patch({ consent: e.target.checked })}
              className="mt-0.5 h-4 w-4 accent-violet-500"
            />
            <span className="flex items-start gap-2 text-sm text-ink-medium">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-violet-300" />
              Tôi xác nhận có quyền dùng hình ảnh/nhân vật này và đồng ý tạo nội dung KOL AI.
            </span>
          </label>
        </div>
      )}
    </div>
  );
}
