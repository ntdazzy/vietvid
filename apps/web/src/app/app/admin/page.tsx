"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Users, Building2, Film, Clapperboard, Coins, ShieldAlert, Search, Loader2, Ban, CircleCheck, Plus } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useMe } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { inputCls } from "@/components/ui/field";

export default function AdminPage() {
  const me = useMe();
  const qc = useQueryClient();
  const isAdmin = me.data?.is_admin;

  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: api.adminStats, enabled: !!isAdmin });
  const moderation = useQuery({ queryKey: ["admin-mod"], queryFn: api.adminModeration, enabled: !!isAdmin });
  const [q, setQ] = useState("");
  const users = useQuery({ queryKey: ["admin-users", q], queryFn: () => api.adminUsers(q), enabled: !!isAdmin });

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

  const S = stats.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">Quản trị</h1>
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
