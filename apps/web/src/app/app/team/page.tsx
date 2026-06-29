"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Crown, Users, ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { useMe } from "@/lib/query/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { FilmLabel } from "@/components/ui/cinematic";
import { Reveal } from "@/components/marketing/reveal";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";
import { MemberRow, avTone, initial } from "@/components/team/member-row";
import { PendingInviteRow } from "@/components/team/pending-invite-row";
import { InviteForm } from "@/components/team/invite-form";

const A = ACCENTS.sky;

export default function TeamPage() {
  const t = useTranslations("team");
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
  // id thành viên đang ở trạng thái "xác nhận xoá" (không xoá thẳng)
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  async function invite(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      await api.inviteMember(email.trim().toLowerCase());
      setEmail("");
      setMsg({ kind: "ok", text: t("inviteSent") });
      qc.invalidateQueries({ queryKey: ["org-invites"] });
    } catch (err) {
      setMsg({ kind: "err", text: err instanceof Error ? err.message : t("inviteError") });
    } finally {
      setBusy(false);
    }
  }

  async function remove(userId: string) {
    setRemovingId(userId);
    try {
      await api.removeMember(userId);
      qc.invalidateQueries({ queryKey: ["org-members"] });
    } finally {
      setRemovingId(null);
      setConfirmId(null);
    }
  }
  async function revoke(id: string) {
    await api.revokeInvite(id);
    qc.invalidateQueries({ queryKey: ["org-invites"] });
  }

  const data = members.data ?? [];
  const nMembers = data.length;
  const nInvites = invites.data?.length ?? 0;
  // avatar-stack: tối đa 6 mặt + đếm phần dư (signature riêng của màn này)
  const stack = data.slice(0, 6);
  const overflow = Math.max(0, nMembers - stack.length);

  return (
    <div className="flex flex-col gap-7">
      {/* ── HEADER RIÊNG: dải glass + glow sky + avatar-stack (KHÔNG dùng CineHero) ── */}
      <Reveal>
        <header className="relative overflow-hidden rounded-3xl glass-bordered">
          <div
            className="pointer-events-none absolute -right-10 -top-16 h-56 w-56 rounded-full blur-3xl"
            style={{ background: A.glow }}
          />
          <div className="relative flex flex-col gap-6 p-6 sm:p-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0">
              <FilmLabel>{t("headerLabel")}</FilmLabel>
              <h1 className="mt-3 font-display text-3xl font-extrabold leading-[1.05] text-ink-high sm:text-[40px]">
                {t("headerTitle")}
              </h1>
              <p className="mt-2 max-w-md text-ink-medium">
                {t("headerSubtitle")}
              </p>

              {/* avatar-stack chồng nhau — chỉ số "người" hiện ra dưới dạng mặt người, không phải con số khô */}
              <div className="mt-6 flex items-center gap-4">
                {members.isLoading ? (
                  <div className="flex -space-x-3">
                    {Array.from({ length: 4 }).map((_, i) => (
                      <Skeleton key={i} className="h-11 w-11 rounded-full ring-2 ring-bg-base" />
                    ))}
                  </div>
                ) : (
                  <div className="flex -space-x-3">
                    {stack.map((m) => (
                      <span
                        key={m.user_id}
                        title={m.full_name || m.email}
                        className={cn(
                          "grid h-11 w-11 place-items-center rounded-full text-sm font-bold ring-2 ring-bg-base",
                          avTone(m.full_name || m.email),
                        )}
                      >
                        {initial(m.full_name || m.email)}
                      </span>
                    ))}
                    {overflow > 0 && (
                      <span className="grid h-11 w-11 place-items-center rounded-full bg-white/[0.06] text-xs font-semibold text-ink-medium ring-2 ring-bg-base">
                        +{overflow}
                      </span>
                    )}
                  </div>
                )}
                <div className="text-sm text-ink-low">
                  <span className="font-numeric text-base font-bold text-ink-high">
                    {members.isLoading ? "—" : nMembers}
                  </span>{" "}
                  {t("membersCountLabel")}
                  {isOwner && nInvites > 0 && (
                    <>
                      {" · "}
                      <span className="font-numeric font-bold text-sky-200">{nInvites}</span> {t("pendingInvitesLabel")}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* nhãn vai trò của chính bạn — đứng riêng góc phải header */}
            <div className="shrink-0">
              <div className={cn("inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-sm", A.chip)}>
                {isOwner ? <Crown className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                <span className="font-medium">{isOwner ? t("youAreOwner") : t("youAreMember")}</span>
              </div>
            </div>
          </div>
        </header>
      </Reveal>

      {/* ── BENTO bất đối xứng: roster rộng (trái) + cột mời hẹp (phải) ── */}
      <div className="grid items-start gap-6 lg:grid-cols-[1.7fr_1fr]">
        {/* ROSTER — danh sách thành viên dạng thẻ-hàng */}
        <Reveal>
          <section className="rounded-3xl glass-bordered p-5 sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <FilmLabel>{t("rosterLabel")}</FilmLabel>
              {!members.isLoading && (
                <span className="font-numeric text-xs text-ink-low">{nMembers}</span>
              )}
            </div>

            {members.isLoading ? (
              <div className="flex flex-col gap-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-2xl" />
                ))}
              </div>
            ) : members.isError ? (
              <div className="rounded-2xl border border-danger/30 bg-danger/[0.06] p-5 text-sm text-danger">
                {t("loadError")}
              </div>
            ) : nMembers === 0 ? (
              <div className="flex flex-col items-center gap-3 py-12 text-center">
                <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white/[0.04]">
                  <Users className="h-6 w-6 text-ink-low" />
                </span>
                <p className="text-sm text-ink-low">{t("emptyRoster")}</p>
              </div>
            ) : (
              <ul className="flex flex-col gap-2">
                {data.map((m) => (
                  <MemberRow
                    key={m.user_id}
                    m={m}
                    canManage={!!isOwner && !m.is_owner}
                    confirming={confirmId === m.user_id}
                    removing={removingId === m.user_id}
                    onAskRemove={() => setConfirmId(m.user_id)}
                    onCancel={() => setConfirmId(null)}
                    onConfirm={() => remove(m.user_id)}
                  />
                ))}
              </ul>
            )}
          </section>
        </Reveal>

        {/* CỘT PHẢI — mời + ghế trống đang chờ (sticky trên desktop) */}
        <div className="flex flex-col gap-6 lg:sticky lg:top-6">
          {isOwner && (
            <InviteForm
              email={email}
              onEmailChange={setEmail}
              busy={busy}
              msg={msg}
              onSubmit={invite}
            />
          )}

          {/* GHẾ TRỐNG ĐANG CHỜ — lời mời chưa nhận, dạng ô viền đứt */}
          {isOwner && nInvites > 0 && (
            <Reveal delay={0.1}>
              <section className="rounded-3xl glass-bordered p-5 sm:p-6">
                <div className="mb-4 flex items-center gap-2">
                  <FilmLabel>{t("pendingLabel")}</FilmLabel>
                  <span className="font-numeric text-xs text-ink-low">{nInvites}</span>
                </div>
                <ul className="flex flex-col gap-2.5">
                  {(invites.data ?? []).map((i) => (
                    <PendingInviteRow key={i.id} i={i} onRevoke={() => revoke(i.id)} />
                  ))}
                </ul>
              </section>
            </Reveal>
          )}
        </div>
      </div>
    </div>
  );
}
