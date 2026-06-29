/**
 * Skeleton khi chuyển màn /app (Next streaming) — khớp layout (hero + lưới), KHÔNG spinner tròn.
 * animate-pulse là CSS → tự đứng yên khi prefers-reduced-motion (global kill).
 */
export default function AppLoading() {
  return (
    <div className="flex animate-pulse flex-col gap-10">
      <div className="h-[300px] rounded-3xl bg-white/[0.04] sm:h-[360px] lg:h-[420px]" />
      <div className="flex flex-col gap-5">
        <div className="h-4 w-40 rounded bg-white/[0.05]" />
        <div className="grid gap-4 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-64 rounded-2xl bg-white/[0.04]" />
          ))}
        </div>
      </div>
    </div>
  );
}
