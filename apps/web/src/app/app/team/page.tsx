"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus, Crown, Trash2, Mail, Loader2, X, Users, MailPlus } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useMe } from "@/lib/query/hooks";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, inputCls } from "@/components/ui/field";
import { ScreenHero, StatTile } from "@/components/app/screen-hero";

const AV_TONES = ["bg-sky-500/20 text-sky-200", "bg-violet-500/20 text-violet-200", "bg-emerald-500/20 text-emerald-200", "bg-rose-500/20 text-rose-200", "bg-amber-500/20 text-amber-200"];
const avTone = (s: string) => AV_TONES[(s.charCodeAt(0) || 0) % AV_TONES.length];

export default function TeamPage() {
  const me = useMe();
  const qc = useQueryClient();
  const isOwner = me.data?.role === "owner";

  const members = useQuery({ queryKey: ["org-members"], queryFn: api.orgMembers });
  const invites = useQuery({
    queryKey: ["org-invites"],
    queryFn: api.orgInvites,
    enabled: isOwner,
  });

  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.inviteMember(email.trim().toLowerCase());
      setEmail("");
      setMsg({ kind: "ok", text: "Đã gửi lời mời." });
      qc.invalidateQueries({ queryKey: ["org-invites"] });
    } catch (err) {
      setMsg({ kind: "err", text: err instanceof Error ? err.message : "Mời lỗi" });
    } finally {
      setBusy(false);
    }
  }

  async function remove(userId: string) {
    await api.removeMember(userId);
    qc.invalidateQueries({ queryKey: ["org-members"] });
  }
  async function revoke(id: string) {
    await api.revokeInvite(id);
    qc.invalidateQueries({ queryKey: ["org-invites"] });
  }

  const nMembers = members.data?.length ?? 0;
  const nInvites = invites.data?.length ?? 0;

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <ScreenHero
        icon={Users}
        accent="sky"
        title="Thành viên"
        sub="Mời cộng sự cùng tạo video trong workspace của bạn."
      >
        <div className="grid grid-cols-2 gap-3 sm:max-w-sm">
          <StatTile icon={Users} label="Đang hoạt động" value={members.isLoading ? "" : nMembers} loading={members.isLoading} accent="sky" />
          <StatTile icon={MailPlus} label="Lời mời chờ" value={isOwner ? nInvites : "—"} accent="amber" />
        </div>
      </ScreenHero>

      {/* mời (chỉ owner) */}
      {isOwner && (
        <GlassCard className="p-5">
          <div className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-ink-low">
            <UserPlus className="h-4 w-4" /> Mời thành viên
          </div>
          <form onSubmit={invite} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Field label="Email">
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-low" />
                  <input
                    type="email"
                    required
                    className={`${inputCls} pl-9`}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="thanhvien@email.com"
                  />
                </div>
              </Field>
            </div>
            <Button type="submit" disabled={busy} className="gap-2">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              Gửi lời mời
            </Button>
          </form>
          {msg && (
            <p className={`mt-2 text-sm ${msg.kind === "ok" ? "text-success" : "text-danger"}`}>
              {msg.text}
            </p>
          )}
        </GlassCard>
      )}

      {/* danh sách thành viên */}
      <GlassCard className="p-5">
        <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-ink-low">
          Đang hoạt động
        </div>
        {members.isLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <div className="flex flex-col divide-y divide-white/[0.06]">
            {(members.data ?? []).map((m) => (
              <div key={m.user_id} className="flex items-center justify-between gap-3 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold ${avTone(m.full_name || m.email)}`}>
                    {(m.full_name || m.email).charAt(0).toUpperCase()}
                  </span>
                  <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-ink-high">
                      {m.full_name || m.email}
                    </span>
                    {m.is_owner ? (
                      <Badge tone="brand">
                        <Crown className="mr-1 h-3 w-3" /> Chủ
                      </Badge>
                    ) : (
                      <Badge tone="neutral">{m.role}</Badge>
                    )}
                  </div>
                  <div className="truncate text-xs text-ink-low">{m.email}</div>
                  </div>
                </div>
                {isOwner && !m.is_owner && (
                  <button
                    onClick={() => remove(m.user_id)}
                    className="grid h-8 w-8 place-items-center rounded-lg text-ink-low hover:bg-danger/10 hover:text-danger"
                    aria-label="Xoá thành viên"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* lời mời đang chờ (owner) */}
      {isOwner && (invites.data?.length ?? 0) > 0 && (
        <GlassCard className="p-5">
          <div className="mb-4 text-sm font-semibold uppercase tracking-wider text-ink-low">
            Lời mời đang chờ
          </div>
          <div className="flex flex-col divide-y divide-white/[0.06]">
            {(invites.data ?? []).map((i) => (
              <div key={i.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <div className="truncate text-sm text-ink-high">{i.email}</div>
                  <div className="text-xs text-ink-low">{i.role} · đang chờ</div>
                </div>
                <button
                  onClick={() => revoke(i.id)}
                  className="grid h-8 w-8 place-items-center rounded-lg text-ink-low hover:bg-white/[0.06] hover:text-ink-medium"
                  aria-label="Thu hồi"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
