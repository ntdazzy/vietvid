import { cn } from "@/lib/utils/cn";

// khoá i18n cho trạng thái job (control-room: dải sức khoẻ render, dùng econ.jobs_by_status thật)
const JOB_STATUS_KEY: Record<string, string> = {
  READY: "jobStatus.ready",
  RUNNING: "jobStatus.running",
  QUEUED: "jobStatus.queued",
  WAITING_CONFIG: "jobStatus.waitingConfig",
  FAILED: "jobStatus.failed",
  QA_FAIL: "jobStatus.qaFail",
  CANCELLED: "jobStatus.cancelled",
  REFUNDED: "jobStatus.refunded",
};

// Băng sức khoẻ render: tỷ lệ từng trạng thái job (dữ liệu thật econ.jobs_by_status).
const STATUS_COLOR: Record<string, string> = {
  READY: "bg-success",
  RUNNING: "bg-violet-400",
  QUEUED: "bg-hold",
  WAITING_CONFIG: "bg-hold/70",
  FAILED: "bg-danger",
  QA_FAIL: "bg-danger/70",
  CANCELLED: "bg-white/20",
  REFUNDED: "bg-refund",
};

export function StatusBar({ byStatus, total, t }: { byStatus: Record<string, number>; total: number; t: (key: string) => string }) {
  const entries = Object.entries(byStatus)
    .filter(([, n]) => n > 0)
    .sort((a, b) => b[1] - a[1]);
  if (total <= 0 || entries.length === 0)
    return <p className="text-sm text-ink-low">{t("noJobsStats")}</p>;

  return (
    <>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-white/[0.04]">
        {entries.map(([status, n]) => (
          <div
            key={status}
            className={cn("h-full transition-all", STATUS_COLOR[status] ?? "bg-white/30")}
            style={{ width: `${(n / total) * 100}%` }}
            title={`${JOB_STATUS_KEY[status] ? t(JOB_STATUS_KEY[status]) : status}: ${n}`}
          />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
        {entries.map(([status, n]) => (
          <span key={status} className="inline-flex items-center gap-1.5 text-xs text-ink-low">
            <span className={cn("h-2 w-2 rounded-full", STATUS_COLOR[status] ?? "bg-white/30")} />
            {JOB_STATUS_KEY[status] ? t(JOB_STATUS_KEY[status]) : status}
            <span className="font-numeric font-semibold text-ink-medium">{n.toLocaleString("vi-VN")}</span>
          </span>
        ))}
      </div>
    </>
  );
}
