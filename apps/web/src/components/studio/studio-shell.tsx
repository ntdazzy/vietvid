"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Clapperboard, ImageIcon, UserRound, Drama, AudioLines, FolderKanban } from "lucide-react";
import { cn } from "@/lib/utils/cn";

// Các "công cụ" studio — rail trái cố định kiểu openart. href trỏ route THẬT (tránh 404);
// character/director tạm trỏ route gần nhất tới khi dựng màn riêng.
const TOOLS = [
  { key: "video", label: "Video", href: "/app/create", icon: Clapperboard },
  { key: "image", label: "Ảnh", href: "/app/image-gen", icon: ImageIcon },
  { key: "kol", label: "KOL", href: "/app/kol", icon: UserRound },
  { key: "character", label: "Nhân vật", href: "/app/character", icon: Drama },
  { key: "audio", label: "Âm thanh", href: "/app/audio", icon: AudioLines },
  { key: "director", label: "Dự án", href: "/app/director", icon: FolderKanban },
];

/** Khung STUDIO 3-vùng kiểu openart: [rail công cụ trái] · [nội dung]. Mỗi màn tạo bọc nội dung
 *  của mình vào đây → rail luôn hiện, đổi công cụ 1 chạm → cảm giác "studio" thay vì trang rời. */
export function StudioShell({ children }: { children: React.ReactNode }) {
  const path = usePathname() || "";
  return (
    <div className="flex gap-5">
      <nav
        aria-label="Công cụ studio"
        className="sticky top-28 hidden h-[calc(100dvh-9rem)] w-[78px] shrink-0 flex-col gap-1 rounded-2xl glass-bordered p-2 lg:flex"
      >
        <span className="px-1 pb-1.5 pt-1 text-center text-[9px] font-semibold uppercase tracking-[0.18em] text-ink-disabled">
          Studio
        </span>
        {TOOLS.map((t) => {
          const active = path.startsWith(t.href);
          const Icon = t.icon;
          return (
            <Link
              key={t.key}
              href={t.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group relative flex flex-col items-center gap-1 rounded-xl px-1 py-2.5 text-[11px] font-medium transition-all duration-200",
                active
                  ? "bg-violet-500/15 text-violet-200 ring-1 ring-violet-400/25 shadow-glow-sm"
                  : "text-ink-low hover:-translate-y-0.5 hover:bg-white/[0.05] hover:text-ink-medium",
              )}
            >
              {active && <span className="absolute left-0 top-1/2 h-6 -translate-y-1/2 rounded-r bg-gradient-to-b from-violet-400 to-indigo-400" style={{ width: 3 }} />}
              <Icon className="h-5 w-5" />
              {t.label}
            </Link>
          );
        })}
      </nav>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
