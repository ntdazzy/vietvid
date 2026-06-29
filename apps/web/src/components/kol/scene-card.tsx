import { ArrowRight, type LucideIcon } from "lucide-react";
import { FilmLabel, CornerFrame } from "@/components/ui/cinematic";

export function SceneCard({ label, icon: Icon, title, desc, cta, onClick }: { label: string; icon: LucideIcon; title: string; desc: string; cta: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="group relative flex flex-col gap-4 overflow-hidden rounded-2xl glass-bordered p-6 text-left transition-all duration-200 hover:-translate-y-1 hover:shadow-glow-sm"
    >
      <CornerFrame color="border-white/10 group-hover:border-rose-300/40" inset="inset-2.5" />
      <div className="flex items-center justify-between">
        <FilmLabel dot={false}>{label}</FilmLabel>
        <ArrowRight className="h-4 w-4 text-ink-low transition-transform duration-200 group-hover:translate-x-1 group-hover:text-rose-200" />
      </div>
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-gradient-to-br from-rose-500/30 to-pink-500/10 text-rose-200 ring-1 ring-rose-400/25">
        <Icon className="h-6 w-6" />
      </span>
      <div>
        <div className="font-display text-lg font-bold text-ink-high">{title}</div>
        <p className="mt-1 text-sm leading-snug text-ink-medium">{desc}</p>
      </div>
      <span className="mt-1 text-sm font-medium text-rose-200">{cta} →</span>
    </button>
  );
}
