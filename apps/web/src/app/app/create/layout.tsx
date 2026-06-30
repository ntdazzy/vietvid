import { AuthGate } from "@/components/shell/auth-gate";

// Trình tạo tốn credit → BẮT BUỘC đăng nhập. Đây là lớp gate client (lớp 2);
// middleware đã chặn server-side khi thiếu cookie phiên. Các màn /app/* khác xem tự do.
export default function CreateLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}
