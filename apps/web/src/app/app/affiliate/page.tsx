"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link2, MousePointerClick, Copy, Check, Trash2, Loader2, Plus, BarChart3 } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls } from "@/components/ui/field";
import { ScreenHero, StatTile } from "@/components/app/screen-hero";

const NETWORKS = ["", "shopee", "lazada", "tiktok"];

export default function AffiliatePage() {
  const qc = useQueryClient();
  const links = useQuery({ queryKey: ["affiliate"], queryFn: api.affiliateLinks });
  const stats = useQuery({ queryKey: ["affiliate-stats"], queryFn: api.affiliateStats });

  const [target, setTarget] = useState("");
  const [label, setLabel] = useState("");
  const [network, setNetwork] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["affiliate"] });
    qc.invalidateQueries({ queryKey: ["affiliate-stats"] });
  };

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.createAffiliateLink({ target_url: target.trim(), label: label.trim(), network });
      setTarget("");
      setLabel("");
      refresh();
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : "Tạo link lỗi");
    } finally {
      setBusy(false);
    }
  }

  async function copy(url: string) {
    await navigator.clipboard.writeText(url);
    setCopied(url);
    setTimeout(() => setCopied(null), 1800);
  }

  const nLinks = stats.data?.links ?? 0;
  const nClicks = stats.data?.clicks ?? 0;
  const avg = nLinks ? Math.round((nClicks / nLinks) * 10) / 10 : 0;

  return (
    <div className="flex flex-col gap-6">
      <ScreenHero
        icon={Link2}
        accent="amber"
        title="Affiliate"
        sub="Gắn link rút gọn vào video, đo click thật về sàn — đóng vòng tới doanh thu."
      >
        <div className="grid grid-cols-3 gap-3">
          <StatTile icon={Link2} label="Link rút gọn" value={nLinks.toLocaleString("vi-VN")} accent="amber" />
          <StatTile icon={MousePointerClick} label="Tổng click" value={nClicks.toLocaleString("vi-VN")} accent="emerald" />
          <StatTile icon={BarChart3} label="Click / link" value={avg.toLocaleString("vi-VN")} accent="amber" />
        </div>
      </ScreenHero>

      <GlassCard className="p-5">
        <form onSubmit={create} className="grid gap-3 sm:grid-cols-2">
          <Field label="Link đích (sản phẩm trên sàn)">
            <input className={inputCls} value={target} onChange={(e) => setTarget(e.target.value)} placeholder="https://shopee.vn/..." />
          </Field>
          <Field label="Nhãn">
            <input className={inputCls} value={label} onChange={(e) => setLabel(e.target.value)} placeholder="VD: Áo thun hè" />
          </Field>
          <Field label="Sàn">
            <select className={inputCls} value={network} onChange={(e) => setNetwork(e.target.value)}>
              {NETWORKS.map((n) => <option key={n} value={n}>{n || "Khác"}</option>)}
            </select>
          </Field>
          <div className="flex items-end">
            <Button type="submit" disabled={busy || !target.trim()} className="gap-2">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />} Tạo link
            </Button>
          </div>
        </form>
        {err && <p className="mt-2 text-sm text-danger">{err}</p>}
      </GlassCard>

      <GlassCard className="p-5">
        {links.isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : (links.data ?? []).length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-low">Chưa có link nào. Tạo link đầu tiên ở trên.</p>
        ) : (
          <div className="flex flex-col divide-y divide-white/[0.06]">
            {(links.data ?? []).map((l) => (
              <div key={l.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-ink-high">{l.label || l.target_url}</span>
                    {l.network && <Badge tone="neutral">{l.network}</Badge>}
                    <Badge tone="brand">{l.clicks} click</Badge>
                  </div>
                  <button onClick={() => copy(l.short_url)} className="mt-0.5 flex items-center gap-1 text-xs text-violet-300 hover:text-violet-200">
                    {copied === l.short_url ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
                    {l.short_url}
                  </button>
                </div>
                <button
                  onClick={async () => { await api.deleteAffiliateLink(l.id); refresh(); }}
                  className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger"
                  aria-label="Xoá link"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}
