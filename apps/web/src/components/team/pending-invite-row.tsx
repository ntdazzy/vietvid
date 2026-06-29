"use client";

import { useTranslations } from "next-intl";
import { MailPlus, X } from "lucide-react";
import type { OrgInvite } from "@/lib/api/types";

/** Một lời mời chưa nhận — ghế trống đang chờ, dạng ô viền đứt. */
export function PendingInviteRow({
  i,
  onRevoke,
}: {
  i: OrgInvite;
  onRevoke: () => void;
}) {
  const t = useTranslations("team");
  return (
    <li
      className="flex items-center gap-3 rounded-2xl border border-dashed border-white/[0.12] bg-white/[0.015] p-3"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-dashed border-sky-400/30 text-sky-200">
        <MailPlus className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm text-ink-high">{i.email}</div>
        <div className="text-xs text-ink-low">{t("inviteNotAccepted")}</div>
      </div>
      <button
        onClick={onRevoke}
        className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low transition hover:bg-white/[0.06] hover:text-ink-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/40"
        aria-label={t("revokeInviteAria", { email: i.email })}
      >
        <X className="h-4 w-4" />
      </button>
    </li>
  );
}
