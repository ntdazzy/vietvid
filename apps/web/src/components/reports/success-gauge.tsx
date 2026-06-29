/** Đồng hồ tròn tỉ lệ thành công — vẽ bằng conic-gradient (không lib chart). */
export function SuccessGauge({ value, ariaLabel }: { value: number; ariaLabel: string }) {
  const deg = (value / 100) * 360;
  return (
    <div
      className="relative grid h-28 w-28 shrink-0 place-items-center rounded-full"
      style={{
        background: `conic-gradient(rgb(52 211 153) ${deg}deg, rgba(255,255,255,0.07) ${deg}deg)`,
      }}
      role="img"
      aria-label={ariaLabel}
    >
      <div className="absolute inset-[10px] rounded-full bg-bg-surface" />
      <div className="relative text-center">
        <div className="font-numeric text-3xl font-extrabold tabular text-ink-high">{value}</div>
        <div className="-mt-1 text-xs text-emerald-300">%</div>
      </div>
    </div>
  );
}
