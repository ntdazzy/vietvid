import { AuthGate } from "@/components/shell/auth-gate";

// Làm hàng loạt = trình tạo tốn credit → BẮT BUỘC đăng nhập (lớp gate client, lớp 2);
// middleware đã chặn server-side khi thiếu cookie phiên. Mirror /app/create/layout.tsx.
export default function BatchLayout({ children }: { children: React.ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}
