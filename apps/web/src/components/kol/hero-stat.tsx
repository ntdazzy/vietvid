export function HeroStat({ n, l }: { n: number; l: string }) {
  return (
    <span className="flex items-baseline gap-1.5">
      <span className="font-numeric text-2xl font-bold tabular text-ink-high">{n}</span>
      <span className="text-sm text-ink-low">{l}</span>
    </span>
  );
}
