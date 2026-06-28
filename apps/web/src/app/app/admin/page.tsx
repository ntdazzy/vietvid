"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Users, Building2, Film, Clapperboard, Coins, ShieldAlert, Search, Loader2, Ban, CircleCheck, Plus, Megaphone, Send, TrendingUp, TrendingDown, Settings2 } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useMe } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";

const vnd = (n: number) => `${n.toLocaleString("vi-VN")}đ`;

export default function AdminPage() {
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
        Bạn không có quyền truy cập trang quản trị.
      </GlassCard>
    );

  async function setStatus(userId: string, status: string) {
    await api.adminSetUserStatus(userId, status);
    qc.invalidateQueries({ queryKey: ["admin-users"] });
  }
  async function adjust(orgId: string) {
    const v = prompt("Cộng/trừ credit (số âm để trừ):", "100");
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
      setBcMsg(`Đã gửi tới ${r.sent} workspace.`);
      setBcTitle("");
      setBcBody("");
    } catch {
      setBcMsg("Gửi thất bại, thử lại.");
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
    setCfgMsg("Đã lưu — áp dụng ngay, không cần deploy.");
    setChain(null);
    setQuota(null);
    qc.invalidateQueries({ queryKey: ["admin-config"] });
    setTimeout(() => setCfgMsg(null), 2500);
  }

  const S = stats.data;
  const E = econ.data;
  const C = cfg.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-grad-brand-soft">
            <ShieldAlert className="h-5 w-5 text-violet-300" />
          </span>
          <h1 className="font-display text-2xl font-bold text-ink-high lg:text-[32px]">Quản trị</h1>
        </div>
        <p className="mt-1 text-ink-low">Vận hành nền tảng: người dùng, credit, kiểm duyệt.</p>
      </div>

      {/* stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Stat icon={Users} label="Người dùng" value={S?.users} />
        <Stat icon={Building2} label="Workspace" value={S?.orgs} />
        <Stat icon={Film} label="Job" value={S?.jobs} />
        <Stat icon={Clapperboard} label="Video" value={S?.videos} />
        <Stat icon={Coins} label="Credit đã phát" value={S?.credits_issued} />
      </div>

      {/* economics: doanh thu vs chi phí → biên lợi nhuận */}
      <div className="grid gap-4 lg:grid-cols-3">
        <GlassCard className="p-5 lg:col-span-2">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
            <TrendingUp className="h-4 w-4 text-violet-300" /> Kinh tế vận hành
          </div>
          {econ.isLoading || !E ? (
            <Skeleton className="h-28 w-full" />
          ) : (
            <>
              <div className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-3">
                <Money label="Doanh thu" value={E.revenue_vnd} tone="ink" />
                <Money label="Chi phí AI" value={E.provider_cost_vnd} tone="warn" sub={`$${E.provider_cost_usd.toLocaleString("en-US")}`} />
                <Money label="Biên lợi nhuận" value={E.margin_vnd} tone={E.margin_vnd >= 0 ? "good" : "bad"} />
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-white/[0.06] pt-4 text-sm">
                <span className="text-ink-low">Tỷ lệ render thành công <span className="ml-1 font-numeric font-semibold text-ink-high">{E.success_rate}%</span></span>
                <span className="text-ink-low">Tổng job <span className="ml-1 font-numeric font-semibold text-ink-high">{E.jobs_total.toLocaleString("vi-VN")}</span></span>
                <span className="text-ink-low">Credit tiêu thụ <span className="ml-1 font-numeric font-semibold text-ink-high">{E.credits_consumed.toLocaleString("vi-VN")}</span></span>
              </div>
            </>
          )}
        </GlassCard>

        {/* broadcast */}
        <GlassCard className="flex flex-col p-5">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
            <Megaphone className="h-4 w-4 text-violet-300" /> Gửi thông báo toàn hệ thống
          </div>
          <input
            className={`${inputCls} mb-2`}
            value={bcTitle}
            onChange={(e) => setBcTitle(e.target.value)}
            maxLength={120}
            placeholder="Tiêu đề (vd: Bảo trì tối nay)"
          />
          <textarea
            className={`${inputCls} mb-3 min-h-[64px] flex-1 resize-y`}
            value={bcBody}
            onChange={(e) => setBcBody(e.target.value)}
            maxLength={500}
            placeholder="Nội dung ngắn (tuỳ chọn)"
          />
          <div className="flex items-center justify-between gap-3">
            {bcMsg ? <span className="text-xs text-success">{bcMsg}</span> : <span />}
            <Button size="sm" variant="glass" className="gap-1.5" onClick={sendBroadcast} disabled={bcBusy || bcTitle.trim().length < 1}>
              {bcBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4 text-violet-300" />} Gửi
            </Button>
          </div>
        </GlassCard>
      </div>

      {/* cấu hình runtime — đổi không cần deploy */}
      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
          <Settings2 className="h-4 w-4 text-violet-300" /> Cấu hình vận hành (áp dụng ngay, không deploy)
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm text-ink-medium">Chuỗi provider video (override)</span>
            <input
              className={inputCls}
              value={chain ?? C?.video_provider_chain ?? ""}
              onChange={(e) => setChain(e.target.value)}
              placeholder="vd: fal,kling,seedance (rỗng = mặc định env)"
            />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm text-ink-medium">Quota API (video/ngày mỗi org, 0 = không giới hạn)</span>
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
            <Settings2 className="h-4 w-4 text-violet-300" /> Lưu cấu hình
          </Button>
          {cfgMsg && <span className="text-xs text-success">{cfgMsg}</span>}
        </div>
      </GlassCard>

      {/* moderation */}
      {(moderation.data?.length ?? 0) > 0 && (
        <GlassCard className="p-5">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-hold">
            <ShieldAlert className="h-4 w-4" /> Chờ kiểm duyệt KOL mặt thật ({moderation.data?.length})
          </div>
          <div className="flex flex-col divide-y divide-white/[0.06]">
            {(moderation.data ?? []).map((m) => (
              <div key={m.id} className="flex items-center justify-between gap-3 py-3">
                <div className="flex items-center gap-3">
                  {m.avatar_url && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={m.avatar_url} alt={m.name} className="h-10 w-10 rounded-lg object-cover" />
                  )}
                  <div>
                    <div className="text-sm font-medium text-ink-high">{m.name}</div>
                    <div className="line-clamp-1 text-xs text-ink-low">{m.description}</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="glass" className="gap-1" onClick={() => moderate(m.id, m.org_id, true)}>
                    <CircleCheck className="h-4 w-4 text-success" /> Duyệt
                  </Button>
                  <Button size="sm" variant="glass" className="gap-1" onClick={() => moderate(m.id, m.org_id, false)}>
                    <Ban className="h-4 w-4 text-danger" /> Chặn
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* users */}
      <GlassCard className="p-5">
        <div className="mb-4 flex items-center gap-2">
          <div className="relative flex-1 max-w-xs">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
            <input className={`${inputCls} pl-9`} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm theo email..." />
          </div>
        </div>
        {users.isLoading ? (
          <Skeleton className="h-40 w-full" />
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
                    <Button size="sm" variant="glass" className="gap-1" onClick={() => adjust(u.org_id!)}>
                      <Plus className="h-3.5 w-3.5" /> Credit
                    </Button>
                  )}
                  {u.status === "ACTIVE" ? (
                    <Button size="sm" variant="glass" className="gap-1" onClick={() => setStatus(u.id, "SUSPENDED")}>
                      <Ban className="h-3.5 w-3.5 text-danger" /> Khoá
                    </Button>
                  ) : (
                    <Button size="sm" variant="glass" className="gap-1" onClick={() => setStatus(u.id, "ACTIVE")}>
                      <CircleCheck className="h-3.5 w-3.5 text-success" /> Mở
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </div>
  );
}

function Money({ label, value, tone, sub }: { label: string; value: number; tone: "ink" | "good" | "bad" | "warn"; sub?: string }) {
  const color = tone === "good" ? "text-success" : tone === "bad" ? "text-danger" : tone === "warn" ? "text-hold" : "text-ink-high";
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-ink-low">{label}</div>
      <div className={`mt-1 flex items-baseline gap-1.5 font-numeric text-xl font-bold ${color}`}>
        {tone === "good" && <TrendingUp className="h-4 w-4" />}
        {tone === "bad" && <TrendingDown className="h-4 w-4" />}
        {vnd(value)}
      </div>
      {sub && <div className="mt-0.5 text-xs text-ink-low">{sub}</div>}
    </div>
  );
}

function Stat({ icon: Icon, label, value }: { icon: typeof Users; label: string; value?: number }) {
  return (
    <GlassCard className="p-4">
      <Icon className="h-5 w-5 text-violet-300" />
      <div className="mt-3 font-numeric text-2xl font-bold text-ink-high">
        {value === undefined ? <Loader2 className="h-5 w-5 animate-spin text-ink-low" /> : value.toLocaleString("vi-VN")}
      </div>
      <div className="mt-0.5 text-sm text-ink-low">{label}</div>
    </GlassCard>
  );
}
