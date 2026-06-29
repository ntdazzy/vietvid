"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Users, Building2, Film, Clapperboard, Coins, ShieldAlert, Search, Loader2, Ban,
  CircleCheck, Plus, Megaphone, Send, TrendingUp, TrendingDown, Settings2, Activity,
  Gauge,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useMe } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import { MiniMoney } from "@/components/admin/mini-money";
import { Gauge3 } from "@/components/admin/gauge3";
import { StatusBar } from "@/components/admin/status-bar";
import { PaymentConfigCard } from "@/components/admin/payment-config-card";

const A = ACCENTS.slate;
const vnd = (n: number) => `${n.toLocaleString("vi-VN")}đ`;

export default function AdminPage() {
  const t = useTranslations("admin");
  const me = useMe();
  const qc = useQueryClient();
  const isAdmin = me.data?.is_admin;

  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: api.adminStats, enabled: !!isAdmin });
  const econ = useQuery({ queryKey: ["admin-econ"], queryFn: api.adminEconomics, enabled: !!isAdmin });
  const cfg = useQuery({ queryKey: ["admin-config"], queryFn: api.adminConfig, enabled: !!isAdmin });
  const moderation = useQuery({ queryKey: ["admin-mod"], queryFn: api.adminModeration, enabled: !!isAdmin });
  const [chain, setChain] = useState<string | null>(null);
  const [quota, setQuota] = useState<string | null>(null);
  const [cfgMsg, setCfgMsg] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const users = useQuery({ queryKey: ["admin-users", q], queryFn: () => api.adminUsers(q), enabled: !!isAdmin });
  const [bcTitle, setBcTitle] = useState("");
  const [bcBody, setBcBody] = useState("");
  const [bcMsg, setBcMsg] = useState<string | null>(null);
  const [bcBusy, setBcBusy] = useState(false);

  if (me.isLoading) return <Skeleton className="h-40 w-full rounded-xl" />;
  if (!isAdmin)
    return (
      <GlassCard className="grid place-items-center gap-2 p-12 text-center text-ink-low">
        <ShieldAlert className="h-8 w-8 text-danger/70" />
        {t("noAccess")}
      </GlassCard>
    );

  async function setStatus(userId: string, status: string) {
    await api.adminSetUserStatus(userId, status);
    qc.invalidateQueries({ queryKey: ["admin-users"] });
  }
  async function adjust(orgId: string) {
    const v = prompt(t("creditPrompt"), "100");
    if (!v) return;
    const amount = parseInt(v, 10);
    if (!Number.isFinite(amount) || amount === 0) return;
    await api.adminCreditAdjust(orgId, amount, "admin");
    qc.invalidateQueries({ queryKey: ["admin-users"] });
  }
  async function moderate(id: string, orgId: string, approve: boolean) {
    await api.adminModerate(id, orgId, approve);
    qc.invalidateQueries({ queryKey: ["admin-mod"] });
  }
  async function sendBroadcast() {
    if (bcTitle.trim().length < 1) return;
    setBcBusy(true);
    setBcMsg(null);
    try {
      const r = await api.adminBroadcast(bcTitle.trim(), bcBody.trim());
      setBcMsg(t("broadcastSent", { count: r.sent }));
      setBcTitle("");
      setBcBody("");
    } catch {
      setBcMsg(t("broadcastFailed"));
    } finally {
      setBcBusy(false);
    }
  }

  async function saveConfig() {
    const patch: { video_provider_chain?: string; max_api_jobs_per_day?: number } = {};
    if (chain !== null) patch.video_provider_chain = chain.trim();
    if (quota !== null) {
      const n = parseInt(quota, 10);
      if (Number.isFinite(n) && n >= 0) patch.max_api_jobs_per_day = n;
    }
    if (Object.keys(patch).length === 0) return;
    await api.adminSetConfig(patch);
    setCfgMsg(t("configSaved"));
    setChain(null);
    setQuota(null);
    qc.invalidateQueries({ queryKey: ["admin-config"] });
    setTimeout(() => setCfgMsg(null), 2500);
  }

  const S = stats.data;
  const E = econ.data;
  const C = cfg.data;
  const pendingCount = moderation.data?.length ?? 0;

  return (
    <div className="flex flex-col gap-7">
      {/* ── BẢNG ĐIỀU KHIỂN — hero split 70/30 (console header trái · verdict kinh tế phải) ── */}
      <section className="grid gap-4 lg:grid-cols-10">
        {/* TRÁI 70 — console header trên nền phòng máy, scrim tối */}
        <div className="relative overflow-hidden rounded-3xl glass-bordered lg:col-span-7">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/bg/desk.jpg" alt="" className="absolute inset-0 h-full w-full object-cover opacity-[0.14]" />
          <div className="absolute inset-0 bg-gradient-to-br from-bg-base via-bg-base/95 to-bg-base/70" />
          <div
            className="pointer-events-none absolute -top-20 -left-10 h-56 w-56 rounded-full blur-3xl"
            style={{ background: A.glow }}
          />
          {/* lưới mảnh — chất "phòng điều khiển" */}
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.05]"
            style={{
              backgroundImage:
                "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
              backgroundSize: "44px 44px",
            }}
          />
          <div className="relative flex min-h-[260px] flex-col justify-between gap-6 p-6 sm:p-8">
            <div className="flex items-center justify-between gap-3">
              <FilmLabel>{t("opsCenter")}</FilmLabel>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.16em] text-ink-low">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success/60" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                </span>
                {t("online")}
              </span>
            </div>
            <div>
              <span className={cn("inline-flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em]", A.text)}>
                <ShieldAlert className="h-3.5 w-3.5" /> {t("platformAdmin")}
              </span>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-4xl lg:text-[44px]">
                {t("heroTitle")}
              </h1>
              <p className="mt-2 max-w-md text-ink-medium">
                {t("heroSubtitle")}
              </p>
            </div>
            {pendingCount > 0 && (
              <a
                href="#kiem-duyet"
                className="inline-flex w-fit items-center gap-2 rounded-xl border border-hold/30 bg-hold/[0.08] px-3.5 py-2 text-sm font-medium text-hold transition hover:bg-hold/[0.14] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hold/40"
              >
                <ShieldAlert className="h-4 w-4" /> {t("pendingReview", { count: pendingCount })}
              </a>
            )}
          </div>
        </div>

        {/* PHẢI 30 — verdict kinh tế: doanh thu → chi phí → biên (dồn đáy, không đối xứng với trái) */}
        <GlassCard bordered className="relative flex flex-col justify-between gap-5 overflow-hidden lg:col-span-3">
          <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
            <Gauge className={cn("h-4 w-4", A.icon)} /> {t("economics")}
          </div>
          {econ.isLoading || !E ? (
            <Skeleton className="h-32 w-full" />
          ) : (
            <div className="flex flex-col gap-4">
              <div>
                <div className="text-xs uppercase tracking-wider text-ink-low">{t("profitMargin")}</div>
                <div
                  className={cn(
                    "mt-1 flex items-baseline gap-1.5 font-numeric text-3xl font-bold tabular",
                    E.margin_vnd >= 0 ? "text-success" : "text-danger",
                  )}
                >
                  {E.margin_vnd >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                  {vnd(E.margin_vnd)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-x-4 gap-y-3 border-t border-white/[0.06] pt-4">
                <MiniMoney label={t("revenue")} value={vnd(E.revenue_vnd)} />
                <MiniMoney label={t("aiCost")} value={vnd(E.provider_cost_vnd)} sub={`$${E.provider_cost_usd.toLocaleString("en-US")}`} tone="hold" />
                <MiniMoney label={t("renderSuccessRate")} value={`${E.success_rate}%`} />
                <MiniMoney label={t("creditsConsumed")} value={E.credits_consumed.toLocaleString("vi-VN")} />
              </div>
            </div>
          )}
        </GlassCard>
      </section>

      {/* ── DÃY ĐỒNG HỒ — 1 panel lớn (người dùng) + dải đo nhỏ, bất đối xứng ── */}
      <Reveal>
        <section className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
          {/* gauge lớn: người dùng — chiếm 2 cột */}
          <GlassCard bordered className="relative flex flex-col justify-between overflow-hidden md:col-span-1 lg:col-span-2">
            <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
              <Users className={cn("h-4 w-4", A.icon)} /> {t("registeredUsers")}
            </div>
            <div className="mt-3 font-numeric text-5xl font-bold tabular text-ink-high">
              {S?.users === undefined ? <Loader2 className="h-7 w-7 animate-spin text-ink-low" /> : S.users.toLocaleString("vi-VN")}
            </div>
            <div className="mt-3 flex items-center gap-2 text-sm text-ink-low">
              <Building2 className="h-4 w-4" />
              <span>
                {S?.orgs === undefined ? t("activeWorkspaces", { count: "…" }) : t("activeWorkspaces", { count: S.orgs.toLocaleString("vi-VN") })}
              </span>
            </div>
          </GlassCard>

          {/* dải đo nhỏ: job / video / credit phát */}
          <Gauge3 icon={Film} label={t("jobsRun")} value={S?.jobs} />
          <Gauge3 icon={Clapperboard} label={t("videosCreated")} value={S?.videos} />
          <Gauge3 icon={Coins} label={t("creditsIssued")} value={S?.credits_issued} />
        </section>
      </Reveal>

      {/* ── BĂNG SỨC KHOẺ RENDER — econ.jobs_by_status (dữ liệu thật, dạng băng tải) ── */}
      {E && Object.keys(E.jobs_by_status).length > 0 && (
        <Reveal>
          <GlassCard className="overflow-hidden">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-ink-low">
                <Activity className={cn("h-4 w-4", A.icon)} /> {t("renderHealth")}
              </div>
              <span className="font-numeric text-xs text-ink-low">{t("jobsCount", { count: E.jobs_total.toLocaleString("vi-VN") })}</span>
            </div>
            <StatusBar byStatus={E.jobs_by_status} total={E.jobs_total} t={t} />
          </GlassCard>
        </Reveal>
      )}

      {/* ── PHƯƠNG THỨC THANH TOÁN (admin cấu hình bank + key, không cần deploy) ── */}
      <Reveal>
        <PaymentConfigCard />
      </Reveal>

      {/* ── SÀN VẬN HÀNH — 2 cột: trái (hàng đợi duyệt + danh sách user) · phải (panel điều khiển) ── */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* TRÁI — chiếm 2 cột */}
        <div className="flex min-w-0 flex-col gap-4 lg:col-span-2">
          {/* hàng đợi kiểm duyệt */}
          {pendingCount > 0 && (
            <GlassCard id="kiem-duyet" className="border-l-2 border-l-hold/50 p-5">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-hold">
                <ShieldAlert className="h-4 w-4" /> {t("moderationQueue", { count: pendingCount })}
              </div>
              <div className="flex flex-col divide-y divide-white/[0.06]">
                {(moderation.data ?? []).map((m) => (
                  <div key={m.id} className="flex items-center justify-between gap-3 py-3">
                    <div className="flex min-w-0 items-center gap-3">
                      <span className="relative grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-lg bg-grad-brand-soft text-sm font-bold text-ink-high ring-1 ring-white/10">
                        {m.name.charAt(0).toUpperCase()}
                        {m.avatar_url && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={m.avatar_url} alt="" onError={(e) => { e.currentTarget.style.display = "none"; }} className="absolute inset-0 h-full w-full object-cover" />
                        )}
                      </span>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-ink-high">{m.name}</div>
                        <div className="line-clamp-1 text-xs text-ink-low">{m.description}</div>
                      </div>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <Button size="sm" variant="glass" className="gap-1" aria-label={t("approveAria", { name: m.name })} onClick={() => moderate(m.id, m.org_id, true)}>
                        <CircleCheck className="h-4 w-4 text-success" /> {t("approve")}
                      </Button>
                      <Button size="sm" variant="glass" className="gap-1" aria-label={t("blockAria", { name: m.name })} onClick={() => moderate(m.id, m.org_id, false)}>
                        <Ban className="h-4 w-4 text-danger" /> {t("block")}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}

          {/* danh sách user */}
          <GlassCard className="p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
                <Users className={cn("h-4 w-4", A.icon)} /> {t("users")}
              </div>
              <div className="relative w-full max-w-xs">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                <input
                  className={`${inputCls} pl-9`}
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder={t("searchPlaceholder")}
                  aria-label={t("searchAria")}
                />
              </div>
            </div>
            {users.isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (users.data?.length ?? 0) === 0 ? (
              <div className="grid place-items-center gap-2 py-10 text-center text-sm text-ink-low">
                <Search className="h-6 w-6 opacity-50" />
                {t("noUsers")}
              </div>
            ) : (
              <div className="flex flex-col divide-y divide-white/[0.06]">
                {(users.data ?? []).map((u) => (
                  <div key={u.id} className="flex items-center justify-between gap-3 py-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-medium text-ink-high">{u.email}</span>
                        {u.status !== "ACTIVE" && <Badge tone="danger">{u.status}</Badge>}
                        {u.plan_code && u.plan_code !== "free" && <Badge tone="brand">{u.plan_code}</Badge>}
                      </div>
                      <div className="text-xs text-ink-low">{u.full_name}</div>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      {u.org_id && (
                        <Button size="sm" variant="glass" className="gap-1" aria-label={t("creditAdjustAria", { email: u.email })} onClick={() => adjust(u.org_id!)}>
                          <Plus className="h-3.5 w-3.5" /> {t("credit")}
                        </Button>
                      )}
                      {u.status === "ACTIVE" ? (
                        <Button size="sm" variant="glass" className="gap-1" aria-label={t("lockAria", { email: u.email })} onClick={() => setStatus(u.id, "SUSPENDED")}>
                          <Ban className="h-3.5 w-3.5 text-danger" /> {t("lock")}
                        </Button>
                      ) : (
                        <Button size="sm" variant="glass" className="gap-1" aria-label={t("unlockAria", { email: u.email })} onClick={() => setStatus(u.id, "ACTIVE")}>
                          <CircleCheck className="h-3.5 w-3.5 text-success" /> {t("unlock")}
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </GlassCard>
        </div>

        {/* PHẢI — panel điều khiển dính (config + broadcast) */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-4 lg:sticky lg:top-24">
            {/* cấu hình runtime */}
            <GlassCard bordered className="p-5">
              <div className="mb-1 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
                <Settings2 className={cn("h-4 w-4", A.icon)} /> {t("runtimeConfig")}
              </div>
              <p className="mb-4 text-xs text-ink-low">{t("appliesInstantly")}</p>
              <div className="flex flex-col gap-4">
                <label className="flex flex-col gap-1.5">
                  <span className="text-sm text-ink-medium">{t("providerChainLabel")}</span>
                  <input
                    className={inputCls}
                    value={chain ?? C?.video_provider_chain ?? ""}
                    onChange={(e) => setChain(e.target.value)}
                    placeholder={t("providerChainPlaceholder")}
                  />
                </label>
                <label className="flex flex-col gap-1.5">
                  <span className="text-sm text-ink-medium">{t("apiQuotaLabel")}</span>
                  <input
                    className={inputCls}
                    type="number"
                    min={0}
                    value={quota ?? (C ? String(C.max_api_jobs_per_day) : "")}
                    onChange={(e) => setQuota(e.target.value)}
                  />
                </label>
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Button size="sm" variant="glass" className="gap-1.5" onClick={saveConfig}>
                  <Settings2 className={cn("h-4 w-4", A.icon)} /> {t("saveConfig")}
                </Button>
                {cfgMsg && <span className="text-xs text-success">{cfgMsg}</span>}
              </div>
            </GlassCard>

            {/* broadcast */}
            <GlassCard className="flex flex-col p-5">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
                <Megaphone className={cn("h-4 w-4", A.icon)} /> {t("broadcast")}
              </div>
              <input
                className={`${inputCls} mb-2`}
                value={bcTitle}
                onChange={(e) => setBcTitle(e.target.value)}
                maxLength={120}
                placeholder={t("broadcastTitlePlaceholder")}
                aria-label={t("broadcastTitleAria")}
              />
              <textarea
                className={`${inputCls} mb-3 min-h-[64px] resize-y`}
                value={bcBody}
                onChange={(e) => setBcBody(e.target.value)}
                maxLength={500}
                placeholder={t("broadcastBodyPlaceholder")}
                aria-label={t("broadcastBodyAria")}
              />
              <div className="flex items-center justify-between gap-3">
                {bcMsg ? <span className="text-xs text-success">{bcMsg}</span> : <span />}
                <Button size="sm" variant="glass" className="gap-1.5" onClick={sendBroadcast} disabled={bcBusy || bcTitle.trim().length < 1}>
                  {bcBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className={cn("h-4 w-4", A.icon)} />} {t("send")}
                </Button>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}
