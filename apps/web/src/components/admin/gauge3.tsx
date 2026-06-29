import { Users, Loader2 } from "lucide-react";
import { GlassCard } from "@/components/ui/glass-card";
import { ACCENTS } from "@/lib/accents";
import { cn } from "@/lib/utils/cn";

const A = ACCENTS.slate;

export function Gauge3({ icon: Icon, label, value }: { icon: typeof Users; label: string; value?: number }) {
  return (
    <GlassCard className="flex flex-col justify-between p-4">
      <Icon className={cn("h-5 w-5", A.icon)} />
      <div className="mt-3 font-numeric text-2xl font-bold tabular text-ink-high">
        {value === undefined ? <Loader2 className="h-5 w-5 animate-spin text-ink-low" /> : value.toLocaleString("vi-VN")}
      </div>
      <div className="mt-0.5 text-sm text-ink-low">{label}</div>
    </GlassCard>
  );
}
