import type { Metadata, Viewport } from "next";
import { Be_Vietnam_Pro, Inter, Space_Grotesk } from "next/font/google";
import { GeistMono } from "geist/font/mono";
import { Providers } from "./providers";
import { NavProgress } from "@/components/shell/nav-progress";
import { getLocale, getMessages } from "@/lib/i18n/server";
import "./globals.css";

// Fonts (mục §0.3): display Việt-chuẩn + body + số credit + mono.
const display = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["600", "700", "800"],
  // italic THẬT (không để browser nghiêng-giả) — nghiêng-giả + bg-clip-text cắt mất
  // phần tràn của chữ HOA nghiêng (vd "AI") ở mép dòng. Sửa gốc cho MỌI heading gradient-italic.
  style: ["normal", "italic"],
  variable: "--font-display",
  display: "swap",
});
const body = Inter({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});
const numeric = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-numeric",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vyra - Tạo mọi loại video bằng AI, giọng Việt thật",
  description:
    "Quảng cáo, KOL, bắt trend, phim ngắn, kể chuyện — Vyra dựng video 60 giây với giọng Việt thật. Minh bạch từng credit, hoàn 100% nếu lỗi hệ thống.",
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
};

export const viewport: Viewport = {
  themeColor: "#06070D",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const locale = getLocale();
  const messages = await getMessages(locale);
  return (
    <html
      lang={locale}
      className={`overflow-x-clip ${display.variable} ${body.variable} ${numeric.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-dvh overflow-x-clip antialiased">
        <NavProgress />
        <Providers locale={locale} messages={messages}>
          {children}
        </Providers>
        <div className="grain" aria-hidden />
      </body>
    </html>
  );
}
