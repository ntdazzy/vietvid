"use client";

import Link from "next/link";
import { LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CreditBadge } from "@/components/shell/credit-badge";
import { CONTENT_GROUPS, MODELS_GROUPS } from "@/lib/features";
import { cn } from "@/lib/utils/cn";
import { PANEL } from "./mega-panel";
import { FeatureRow } from "./feature-row";

export function MobileMenu({
  isAuthed,
  isAdmin,
  onClose,
  onLogout,
}: {
  isAuthed: boolean;
  isAdmin: boolean;
  onClose: () => void;
  onLogout: () => void;
}) {
  return (
    <div className="mx-auto mt-2 max-w-[1600px] px-4 lg:hidden">
      <div className={cn(PANEL, "max-h-[78vh] overflow-y-auto p-3")}>
        {isAuthed && (
          <div className="mb-3">
            <div className="mb-2 flex items-center justify-between px-1">
              <CreditBadge />
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                ["Bảng điều khiển", "/app"],
                ["KOL AI", "/app/kol"],
                ["Mẫu", "/app/templates"],
                ["Thư viện", "/app/library"],
                ["Affiliate", "/app/affiliate"],
                ["Báo cáo", "/app/reports"],
                ["API", "/app/api"],
                ...(isAdmin ? ([["Admin", "/app/admin"]] as [string, string][]) : []),
              ].map(([t, h]) => (
                <Link
                  key={h}
                  href={h}
                  onClick={onClose}
                  className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2 text-sm font-medium text-ink-medium hover:bg-white/[0.05] hover:text-ink-high"
                >
                  {t}
                </Link>
              ))}
            </div>
          </div>
        )}
        {[...CONTENT_GROUPS, ...MODELS_GROUPS].map((g) => (
          <div key={g.title} className="mb-3">
            <div className="flex items-center gap-2 px-2 pb-1">
              <span className="h-[3px] w-4 rounded-full bg-grad-brand" />
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-300/80">
                {g.title}
              </span>
            </div>
            {g.items.map((f) => (
              <FeatureRow key={f.key} f={f} onNav={onClose} />
            ))}
          </div>
        ))}
        <Link
          href="/pricing"
          onClick={onClose}
          className="mb-2 block rounded-lg border border-white/[0.06] bg-white/[0.02] px-3 py-2.5 text-center text-sm font-medium text-ink-medium hover:bg-white/[0.05] hover:text-ink-high"
        >
          Bảng giá
        </Link>
        <Link href={isAuthed ? "/app/create" : "/login"} onClick={onClose}>
          <Button className="mt-1 w-full">{isAuthed ? "Tạo nội dung" : "Đăng nhập"}</Button>
        </Link>
        {isAuthed && (
          <button
            onClick={onLogout}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg py-2 text-sm text-ink-low hover:bg-white/[0.05] hover:text-ink-medium"
          >
            <LogOut className="h-4 w-4" /> Đăng xuất
          </button>
        )}
      </div>
    </div>
  );
}
