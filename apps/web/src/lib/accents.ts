// Bảng accent dùng chung (không "use client") — màn quản trị + feature page đều xài.
// Mỗi màn/feature 1 accent riêng → nhìn lướt là phân biệt được, vẫn chung brand dark+glass.
export type Accent = "violet" | "emerald" | "amber" | "sky" | "rose" | "cyan" | "slate";

export const ACCENTS: Record<Accent, { tile: string; icon: string; glow: string; ring: string; line: string; chip: string; text: string; grad: string; bar: string }> = {
  violet: { tile: "from-violet-500/30 to-indigo-500/10", icon: "text-violet-200", glow: "rgba(124,77,255,0.20)", ring: "ring-violet-400/25", line: "via-violet-500/60", chip: "bg-violet-500/15 text-violet-200 border-violet-400/30", text: "text-violet-300", grad: "from-violet-500 to-indigo-500", bar: "bg-violet-400/70" },
  emerald: { tile: "from-emerald-500/30 to-teal-500/10", icon: "text-emerald-200", glow: "rgba(16,185,129,0.18)", ring: "ring-emerald-400/25", line: "via-emerald-500/60", chip: "bg-emerald-500/15 text-emerald-200 border-emerald-400/30", text: "text-emerald-300", grad: "from-emerald-500 to-teal-500", bar: "bg-emerald-400/70" },
  amber: { tile: "from-amber-500/30 to-orange-500/10", icon: "text-amber-200", glow: "rgba(245,158,11,0.18)", ring: "ring-amber-400/25", line: "via-amber-500/60", chip: "bg-amber-500/15 text-amber-200 border-amber-400/30", text: "text-amber-300", grad: "from-amber-500 to-orange-500", bar: "bg-amber-400/70" },
  sky: { tile: "from-sky-500/30 to-blue-500/10", icon: "text-sky-200", glow: "rgba(56,189,248,0.18)", ring: "ring-sky-400/25", line: "via-sky-500/60", chip: "bg-sky-500/15 text-sky-200 border-sky-400/30", text: "text-sky-300", grad: "from-sky-500 to-blue-500", bar: "bg-sky-400/70" },
  rose: { tile: "from-rose-500/30 to-pink-500/10", icon: "text-rose-200", glow: "rgba(244,63,94,0.18)", ring: "ring-rose-400/25", line: "via-rose-500/60", chip: "bg-rose-500/15 text-rose-200 border-rose-400/30", text: "text-rose-300", grad: "from-rose-500 to-pink-500", bar: "bg-rose-400/70" },
  cyan: { tile: "from-cyan-500/30 to-teal-500/10", icon: "text-cyan-200", glow: "rgba(34,211,238,0.18)", ring: "ring-cyan-400/25", line: "via-cyan-500/60", chip: "bg-cyan-500/15 text-cyan-200 border-cyan-400/30", text: "text-cyan-300", grad: "from-cyan-500 to-teal-500", bar: "bg-cyan-400/70" },
  slate: { tile: "from-slate-400/25 to-slate-500/10", icon: "text-slate-200", glow: "rgba(148,163,184,0.16)", ring: "ring-slate-300/20", line: "via-slate-400/60", chip: "bg-slate-400/15 text-slate-200 border-slate-300/25", text: "text-slate-300", grad: "from-slate-400 to-slate-500", bar: "bg-slate-400/70" },
};
