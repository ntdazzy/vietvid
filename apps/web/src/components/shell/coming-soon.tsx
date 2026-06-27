import { Construction } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

/** Placeholder on-brand cho màn chưa dựng (W1+). */
export function ComingSoon({
  title,
  milestone,
  desc,
}: {
  title: string;
  milestone: string;
  desc: string;
}) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-ink-high lg:text-[34px]">{title}</h1>
        <Badge tone="brand">{milestone}</Badge>
      </div>
      <GlassCard bordered className="flex flex-col items-center gap-4 py-20 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-2xl bg-grad-brand-soft">
          <Construction className="h-7 w-7 text-violet-300" />
        </div>
        <p className="max-w-md text-ink-low">{desc}</p>
      </GlassCard>
    </div>
  );
}
