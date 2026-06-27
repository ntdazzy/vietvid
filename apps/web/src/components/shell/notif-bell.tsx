"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, Film, CreditCard, Info } from "lucide-react";
import { api } from "@/lib/api/endpoints";
import { cn } from "@/lib/utils/cn";

const ICON: Record<string, typeof Film> = {
  job_ready: Film,
  job_failed: Film,
  payment: CreditCard,
  system: Info,
};

export function NotifBell() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const notif = useQuery({ queryKey: ["notifs"], queryFn: api.notifications, refetchInterval: 30_000 });
  const unread = notif.data?.unread ?? 0;

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && unread > 0) {
      await api.markNotificationsRead();
      qc.invalidateQueries({ queryKey: ["notifs"] });
    }
  }

  return (
    <div className="relative" onMouseLeave={() => setOpen(false)}>
      <button
        onClick={toggle}
        className="relative grid h-9 w-9 place-items-center rounded-lg text-ink-medium hover:bg-white/[0.05] hover:text-ink-high"
        aria-label="Thông báo"
      >
        <Bell className="h-[18px] w-[18px]" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-violet-500 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 w-80 pt-2">
          <div className="rounded-2xl border border-white/[0.1] bg-bg-elevated/95 p-2 shadow-[0_24px_70px_-20px_rgba(0,0,0,0.8)] backdrop-blur-2xl">
            <div className="flex items-center justify-between px-2 pb-2 pt-1 text-xs font-semibold uppercase tracking-wider text-ink-low">
              Thông báo
              <CheckCheck className="h-3.5 w-3.5" />
            </div>
            <div className="max-h-[60vh] overflow-y-auto">
              {(notif.data?.items ?? []).length === 0 ? (
                <p className="px-3 py-6 text-center text-sm text-ink-low">Chưa có thông báo.</p>
              ) : (
                (notif.data?.items ?? []).map((n) => {
                  const Icon = ICON[n.type] ?? Info;
                  const href = n.ref_type === "job" ? `/app/v/${n.ref_id}` : "/app/billing";
                  return (
                    <Link
                      key={n.id}
                      href={href}
                      onClick={() => setOpen(false)}
                      className={cn(
                        "flex items-start gap-3 rounded-lg p-2.5 hover:bg-white/[0.05]",
                        !n.read && "bg-violet-500/[0.06]",
                      )}
                    >
                      <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-grad-brand-soft text-violet-300">
                        <Icon className="h-4 w-4" />
                      </span>
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-ink-high">{n.title}</div>
                        <div className="line-clamp-2 text-xs text-ink-low">{n.body}</div>
                      </div>
                    </Link>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
