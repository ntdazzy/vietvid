"use client";

import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export function NavLink({
  href,
  children,
  onEnter,
}: {
  href: string;
  children: React.ReactNode;
  onEnter?: () => void;
}) {
  return (
    <Link
      href={href}
      onMouseEnter={onEnter}
      className="whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium text-ink-medium outline-none transition-colors hover:bg-white/[0.05] hover:text-ink-high focus-visible:ring-2 focus-visible:ring-violet-400/60"
    >
      {children}
    </Link>
  );
}

export function Trigger({ label, active, onEnter }: { label: string; active: boolean; onEnter: () => void }) {
  return (
    <button
      onMouseEnter={onEnter}
      aria-haspopup="true"
      aria-expanded={active}
      className={cn(
        "flex items-center gap-1 whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium outline-none transition-colors hover:bg-white/[0.05] focus-visible:ring-2 focus-visible:ring-violet-400/60",
        active ? "text-ink-high" : "text-ink-medium hover:text-ink-high",
      )}
    >
      {label}
      <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", active && "rotate-180")} />
    </button>
  );
}
