"use client";

import { useTranslations } from "next-intl";
import { Crown, Trash2, Loader2, X, Check } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { OrgMember } from "@/lib/api/types";

// Tô màu avatar theo chữ cái đầu — ổn định, nhiều màu để roster đỡ đơn điệu.
export const AV_TONES = [
  "bg-sky-500/20 text-sky-100 ring-sky-400/30",
  "bg-violet-500/20 text-violet-100 ring-violet-400/30",
  "bg-emerald-500/20 text-emerald-100 ring-emerald-400/30",
  "bg-rose-500/20 text-rose-100 ring-rose-400/30",
  "bg-cyan-500/20 text-cyan-100 ring-cyan-400/30",
];
export const avTone = (s: string) => AV_TONES[(s.charCodeAt(0) || 0) % AV_TONES.length];
export const initial = (s: string) => (s || "?").charAt(0).toUpperCase();

/** Một hàng thành viên trong roster. Xoá phải xác nhận inline (không xoá thẳng). */
export function MemberRow({
  m,
  canManage,
  confirming,
  removing,
  onAskRemove,
  onCancel,
  onConfirm,
}: {
  m: OrgMember;
  canManage: boolean;
  confirming: boolean;
  removing: boolean;
  onAskRemove: () => void;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const t = useTranslations("team");
  const name = m.full_name || m.email;
  return (
    <li
      className={cn(
        "group flex items-center gap-3 rounded-2xl border border-white/[0.05] bg-white/[0.02] p-3 transition-colors",
        confirming ? "border-danger/30 bg-danger/[0.05]" : "hover:border-white/[0.1] hover:bg-white/[0.035]",
      )}
    >
      <span
        className={cn(
          "grid h-11 w-11 shrink-0 place-items-center rounded-full text-sm font-bold ring-1",
          avTone(name),
        )}
      >
        {initial(name)}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-ink-high">{name}</span>
          {m.is_owner ? (
            <span className="inline-flex shrink-0 items-center gap-1 rounded-full border border-violet-500/30 bg-violet-500/14 px-2 py-0.5 text-[11px] font-medium text-violet-300">
              <Crown className="h-3 w-3" /> {t("ownerBadge")}
            </span>
          ) : (
            <span className="shrink-0 rounded-full border border-white/[0.08] bg-white/[0.06] px-2 py-0.5 text-[11px] text-ink-medium">
              {t("memberBadge")}
            </span>
          )}
        </div>
        <div className="truncate text-xs text-ink-low">{m.email}</div>
      </div>

      {canManage && !confirming && (
        <button
          onClick={onAskRemove}
          className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-ink-low opacity-0 transition hover:bg-danger/10 hover:text-danger focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/40 group-hover:opacity-100"
          aria-label={t("removeMemberAria", { name })}
        >
          <Trash2 className="h-4 w-4" />
        </button>
      )}

      {canManage && confirming && (
        <div className="flex shrink-0 items-center gap-1.5">
          <span className="hidden text-xs text-danger sm:inline">{t("removeConfirmPrompt")}</span>
          <button
            onClick={onConfirm}
            disabled={removing}
            className="inline-flex h-8 items-center gap-1 rounded-lg bg-danger/15 px-2.5 text-xs font-medium text-danger transition hover:bg-danger/25 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger/40"
            aria-label={t("confirmRemoveAria", { name })}
          >
            {removing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
            {t("removeButton")}
          </button>
          <button
            onClick={onCancel}
            disabled={removing}
            className="grid h-8 w-8 place-items-center rounded-lg text-ink-low transition hover:bg-white/[0.06] hover:text-ink-high disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
            aria-label={t("cancelRemoveAria")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </li>
  );
}
