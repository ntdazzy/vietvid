import { SiteHeader } from "@/components/marketing/site-header";

// Mọi màn /app/* xem TỰ DO (không ép đăng nhập) — header tự nhận trạng thái phiên
// thật (khách thấy nút "Đăng nhập", đã đăng nhập thấy credit + Tạo video). Chỉ trình
// tạo (/app/create) mới gate (xem create/layout.tsx + middleware).
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-dvh mesh-bg">
      <SiteHeader />
      <main className="mx-auto w-full max-w-6xl overflow-x-clip px-4 pb-20 pt-28 lg:px-8">{children}</main>
    </div>
  );
}
