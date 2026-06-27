import type { JobStatus } from "@/lib/api/types";

export type Tone = "neutral" | "brand" | "hold" | "success" | "refund" | "danger";

const TONE: Record<string, Tone> = {
  READY: "success",
  FAILED: "danger",
  QA_FAIL: "danger",
  REFUNDED: "refund",
  CANCELLED: "neutral",
  QUEUED: "hold",
  HELD: "hold",
  WAITING_CONFIG: "hold",
  RUNNING: "brand",
};

const LABEL: Record<string, string> = {
  READY: "Hoàn tất",
  FAILED: "Lỗi hệ thống",
  QA_FAIL: "Chưa đạt",
  REFUNDED: "Đã hoàn",
  CANCELLED: "Đã huỷ",
  QUEUED: "Trong hàng đợi",
  HELD: "Đang giữ",
  WAITING_CONFIG: "Chờ cấu hình",
  RUNNING: "Đang tạo",
};

export const statusTone = (s: JobStatus): Tone => TONE[s] ?? "neutral";
export const statusLabel = (s: JobStatus): string => LABEL[s] ?? s;

export function formatDate(iso?: string | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}
