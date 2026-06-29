"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  MousePointerClick,
  Loader2,
  Plus,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import { FunnelMeter } from "@/components/affiliate/funnel-meter";
import { EmptyState } from "@/components/affiliate/empty-state";
import { AffiliateLinkCard } from "@/components/affiliate/affiliate-link-card";

const NETWORKS = ["", "shopee", "lazada", "tiktok"];
const a = ACCENTS.amber;

export default function AffiliatePage() {
  const t = useTranslations("affiliate");
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
      setErr(e2 instanceof Error ? e2.message : t("createError"));
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
  const statLoading = stats.isLoading;

  const list = links.data ?? [];
  // link nhiều click nhất → để dẫn đầu cột phải, phần còn lại giữ thứ tự gốc.
  const sorted = [...list].sort((x, y) => y.clicks - x.clicks);

  return (
    <div className="flex flex-col gap-7">
      {/* ── PANEL ĐẦU MÀN: phễu click → đơn (signature riêng của Affiliate) ── */}
      <Reveal>
        <section className="relative overflow-hidden rounded-3xl glass-bordered">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/showcase/affiliate.jpg"
            alt=""
            className="absolute inset-0 h-full w-full object-cover opacity-25"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-bg-base via-bg-base/92 to-bg-base/45" />
          <div
            className="pointer-events-none absolute -top-20 right-10 h-56 w-56 rounded-full blur-3xl"
            style={{ background: a.glow }}
          />

          <div className="relative grid gap-8 p-6 sm:p-8 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:p-10">
            {/* trái — định vị */}
            <div className="max-w-lg">
              <FilmLabel>{t("heroEyebrow")}</FilmLabel>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.06] text-ink-high sm:text-4xl lg:text-[44px]">
                {t.rich("heroTitle", {
                  br: () => <br />,
                  grad: (chunks) => (
                    <span className="bg-gradient-to-r from-amber-300 to-orange-400 bg-clip-text text-transparent">
                      {chunks}
                    </span>
                  ),
                })}
              </h1>
              <p className="mt-3 text-ink-medium sm:text-lg">
                {t("heroDesc")}
              </p>
            </div>

            {/* phải — phễu 2 tầng dựng từ số thật */}
            <FunnelMeter clicks={nClicks} links={nLinks} loading={statLoading} />
          </div>
        </section>
      </Reveal>

      {/* ── HAI CỘT: tạo link (trái dính) + danh sách link (phải) ── */}
      <div className="grid gap-6 lg:grid-cols-[360px_1fr] lg:items-start">
        {/* CỘT TRÁI — form tạo + tỉ lệ trung bình */}
        <div className="flex flex-col gap-5 lg:sticky lg:top-24">
          <Reveal delay={0.05}>
            <div className="relative overflow-hidden rounded-2xl glass-bordered p-5">
              <div className="mb-4 flex items-center gap-2.5">
                <span
                  className={cn(
                    "grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br ring-1",
                    a.tile,
                    a.ring,
                  )}
                >
                  <Plus className="h-4.5 w-4.5 text-amber-200" />
                </span>
                <div>
                  <div className="font-display text-sm font-semibold text-ink-high">{t("newLinkTitle")}</div>
                  <div className="text-xs text-ink-low">{t("newLinkSub")}</div>
                </div>
              </div>

              <form onSubmit={create} className="flex flex-col gap-3">
                <Field label={t("targetLabel")}>
                  <input
                    className={inputCls}
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    placeholder="https://shopee.vn/..."
                  />
                </Field>
                <Field label={t("nameLabel")}>
                  <input
                    className={inputCls}
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    placeholder={t("namePlaceholder")}
                  />
                </Field>
                <Field label={t("networkLabel")}>
                  <select
                    className={inputCls}
                    value={network}
                    onChange={(e) => setNetwork(e.target.value)}
                  >
                    {NETWORKS.map((n) => (
                      <option key={n} value={n}>
                        {n || t("networkOther")}
                      </option>
                    ))}
                  </select>
                </Field>
                <Button type="submit" disabled={busy || !target.trim()} className="mt-1 w-full gap-2">
                  {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  {t("createButton")}
                </Button>
              </form>
              {err && <p className="mt-2 text-sm text-danger">{err}</p>}
            </div>
          </Reveal>

          {/* ô tỉ lệ trung bình — số thật, gắn với cột */}
          <Reveal delay={0.1}>
            <div className="rounded-2xl glass-bordered p-5">
              <div className="flex items-center gap-1.5 text-xs uppercase tracking-[0.16em] text-ink-low">
                <MousePointerClick className="h-3.5 w-3.5 text-amber-200" /> {t("avgEyebrow")}
              </div>
              <div className="mt-2 flex items-end gap-2">
                <span className="font-numeric text-4xl font-bold tabular text-ink-high">
                  {statLoading ? (
                    <span className="inline-block h-9 w-16 animate-pulse rounded bg-white/[0.06]" />
                  ) : (
                    avg.toLocaleString("vi-VN")
                  )}
                </span>
                <span className="mb-1 text-sm text-ink-low">{t("avgUnit")}</span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-ink-low">
                {t("avgNote", { count: nLinks.toLocaleString("vi-VN") })}
              </p>
            </div>
          </Reveal>
        </div>

        {/* CỘT PHẢI — danh sách short-link dạng thẻ hover */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <FilmLabel>{t("activeLinks")}</FilmLabel>
            {!links.isLoading && list.length > 0 && (
              <span className="text-xs text-ink-low">{t("linkCount", { count: list.length })}</span>
            )}
          </div>

          {links.isLoading ? (
            <div className="grid gap-3">
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
              <Skeleton className="h-20 w-full rounded-2xl" />
            </div>
          ) : list.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-3">
              {sorted.map((l, i) => {
                const top = list.length > 1 && i === 0 && l.clicks > 0;
                return (
                  <Reveal key={l.id} delay={Math.min(i * 0.04, 0.24)}>
                    <AffiliateLinkCard
                      link={l}
                      maxClicks={sorted[0].clicks}
                      top={top}
                      copied={copied}
                      onCopy={copy}
                      onDelete={async () => {
                        await api.deleteAffiliateLink(l.id);
                        refresh();
                      }}
                    />
                  </Reveal>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
