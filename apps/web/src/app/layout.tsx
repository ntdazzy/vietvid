import type { Metadata, Viewport } from "next";
import { Be_Vietnam_Pro, Inter, Space_Grotesk } from "next/font/google";
import { GeistMono } from "geist/font/mono";
import { Providers } from "./providers";
import "./globals.css";

// Fonts (mục §0.3): display Việt-chuẩn + body + số credit + mono.
const display = Be_Vietnam_Pro({
  subsets: ["latin", "vietnamese"],
  weight: ["600", "700", "800"],
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
  title: "Vyra - Tạo video bán hàng, giọng Việt thật",
  description:
    "1 ảnh sản phẩm → video quảng cáo 60 giây. Giọng Việt thật, minh bạch từng credit, hoàn 100% nếu lỗi hệ thống.",
};

export const viewport: Viewport = {
  themeColor: "#06070D",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="vi"
      className={`${display.variable} ${body.variable} ${numeric.variable} ${GeistMono.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-dvh antialiased">
        <Providers>{children}</Providers>
        <div className="grain" aria-hidden />
      </body>
    </html>
  );
}
