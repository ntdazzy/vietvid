"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Sparkles, Link2, X, AlertCircle, Layers } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import { StudioShell } from "@/components/studio/studio-shell";
import { Button } from "@/components/ui/button";
import { ChipGroup, inputCls } from "@/components/ui/field";
import { cn } from "@/lib/utils/cn";

type Item = { link: string; name: string; price: string; description: string; image_url?: string };

// LÀM HÀNG LOẠT: dán nhiều link SP → nhập tất cả → tạo N video 1 lượt (mỗi SP 1 clip).
// Điểm khác biệt vs autovis (họ chỉ tạo từng cái). Gọi /v1/batch (atomic credit hold cả loạt).
export default function BatchPage() {
  const router = useRouter();
  const [linksText, setLinksText] = useState("");
  const [items, setItems] = useState<Item[]>([]);
  const [importing, setImporting] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insufficient, setInsufficient] = useState(false);
  const [seconds, setSeconds] = useState(8);
  const [resolution, setResolution] = useState("720p");
  const [aspect, setAspect] = useState("9:16");
  const [voiceGender, setVoiceGender] = useState("female");

  const links = linksText.split("\n").map((l) => l.trim()).filter((l) => /^https?:\/\//.test(l));

  async function importAll() {
    if (!links.length) return;
    setImporting(true);
    setError(null);
    try {
      const got = await Promise.all(
        links.map(async (link) => {
          try {
            const d = await api.importProduct(link);
            return {
              link,
              name: d.name || "",
              price: d.price ? `${Number(d.price).toLocaleString("vi-VN")}đ` : "",
              description: d.description || "",
              image_url: d.image_url,
            } as Item;
          } catch {
            return { link, name: "", price: "", description: "" } as Item; // giữ dòng để user tự điền
          }
        }),
      );
      setItems(got);
    } finally {
      setImporting(false);
    }
  }

  function patchItem(i: number, patch: Partial<Item>) {
    setItems((xs) => xs.map((x, idx) => (idx === i ? { ...x, ...patch } : x)));
  }
  function removeItem(i: number) {
    setItems((xs) => xs.filter((_, idx) => idx !== i));
  }

  const ready = items.filter((it) => it.name.trim());

  async function create() {
    if (ready.length < 2) {
      setError("Cần ít nhất 2 sản phẩm (có tên) để làm hàng loạt.");
      return;
    }
    setCreating(true);
    setError(null);
    setInsufficient(false);
    try {
      const res = await api.batchCreate({
        idempotency_key: crypto.randomUUID(),
        mode: "product_ad",
        seconds,
        resolution,
        aspect,
        voice_gender: voiceGender,
        items: ready.map((it) => ({
          product: { name: it.name, price: it.price, description: it.description },
        })),
      });
      router.push(`/app/series/${res.batch_group}`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 402) setInsufficient(true);
      else setError(e instanceof Error ? e.message : "Tạo loạt video thất bại.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <StudioShell>
      <div className="mx-auto flex max-w-3xl flex-col gap-6 pb-24">
        <div>
          <div className="flex items-center gap-2 text-violet-300">
            <Layers className="h-5 w-5" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">Làm hàng loạt</span>
          </div>
          <h1 className="mt-2 font-display text-2xl font-bold text-ink-high">
            Dán nhiều link → ra nhiều video một lượt
          </h1>
          <p className="mt-1 text-sm text-ink-low">
            Mỗi link 1 sản phẩm → 1 video bán hàng. Dán tối đa 20 link (mỗi link 1 dòng).
          </p>
        </div>

        {/* Nhập link hàng loạt */}
        <div className="rounded-xl border border-violet-500/20 bg-violet-500/[0.04] p-4">
          <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-violet-200">
            <Link2 className="h-3.5 w-3.5" /> Danh sách link sản phẩm (mỗi dòng 1 link)
          </div>
          <textarea
            className={cn(inputCls, "min-h-[120px] resize-y font-mono text-xs")}
            value={linksText}
            onChange={(e) => setLinksText(e.target.value)}
            placeholder={"https://shopee.vn/...\nhttps://shopee.vn/...\nhttps://www.tiktok.com/..."}
          />
          <div className="mt-2 flex items-center justify-between">
            <span className="text-[11px] text-ink-low">{links.length} link hợp lệ</span>
            <Button variant="glass" onClick={importAll} disabled={importing || !links.length} className="gap-1.5">
              {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4 text-violet-300" />}
              Nhập tất cả
            </Button>
          </div>
        </div>

        {/* Danh sách SP đã nhập */}
        {items.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="text-xs font-medium text-ink-medium">{ready.length}/{items.length} sản phẩm sẵn sàng</div>
            {items.map((it, i) => (
              <div key={i} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-2.5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                {it.image_url ? (
                  <img src={it.image_url} alt="" className="h-12 w-12 shrink-0 rounded-lg object-cover" />
                ) : (
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-white/[0.04] text-ink-low">?</div>
                )}
                <div className="grid flex-1 gap-1.5 sm:grid-cols-2">
                  <input
                    className={cn(inputCls, "py-1.5 text-sm")}
                    value={it.name}
                    onChange={(e) => patchItem(i, { name: e.target.value })}
                    placeholder="Tên sản phẩm"
                  />
                  <input
                    className={cn(inputCls, "py-1.5 text-sm")}
                    value={it.price}
                    onChange={(e) => patchItem(i, { price: e.target.value })}
                    placeholder="Giá"
                  />
                </div>
                <button onClick={() => removeItem(i)} className="shrink-0 rounded-lg p-1.5 text-ink-low hover:bg-white/[0.05] hover:text-danger" aria-label="Xoá">
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Cài đặt chung + tạo */}
        {items.length > 0 && (
          <div className="flex flex-col gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <div className="mb-1.5 text-xs font-medium text-ink-medium">Thời lượng</div>
                <ChipGroup value={seconds} onChange={(v) => setSeconds(v as number)} options={[5, 8, 10, 15].map((s) => ({ value: s, label: `${s}s` }))} />
              </div>
              <div>
                <div className="mb-1.5 text-xs font-medium text-ink-medium">Tỉ lệ</div>
                <ChipGroup value={aspect} onChange={(v) => setAspect(v as string)} options={[{ value: "9:16", label: "9:16" }, { value: "1:1", label: "1:1" }, { value: "16:9", label: "16:9" }]} />
              </div>
              <div>
                <div className="mb-1.5 text-xs font-medium text-ink-medium">Độ nét</div>
                <ChipGroup value={resolution} onChange={(v) => setResolution(v as string)} options={[{ value: "480p", label: "480p" }, { value: "720p", label: "720p" }, { value: "1080p", label: "1080p" }]} />
              </div>
              <div>
                <div className="mb-1.5 text-xs font-medium text-ink-medium">Giọng</div>
                <ChipGroup value={voiceGender} onChange={(v) => setVoiceGender(v as string)} options={[{ value: "female", label: "Nữ" }, { value: "male", label: "Nam" }]} />
              </div>
            </div>

            {insufficient && (
              <div className="flex items-center justify-between gap-3 rounded-xl border border-hold/30 bg-hold/[0.1] px-4 py-3 text-sm text-hold">
                <span className="flex items-center gap-2"><AlertCircle className="h-4 w-4" /> Không đủ credit cho cả loạt.</span>
                <Link href="/app/billing" className="font-medium underline">Nạp thêm</Link>
              </div>
            )}
            {error && <p className="flex items-center gap-2 text-sm text-danger"><AlertCircle className="h-4 w-4" /> {error}</p>}

            <Button onClick={create} disabled={creating || ready.length < 2} className="gap-2 self-end">
              {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {creating ? "Đang tạo..." : `Tạo ${ready.length} video`}
            </Button>
          </div>
        )}
      </div>
    </StudioShell>
  );
}
