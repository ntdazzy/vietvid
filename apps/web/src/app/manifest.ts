import type { MetadataRoute } from "next";

// PWA manifest — cho phép "Thêm vào màn hình chính" trên mobile + cài như app.
// Next tự phục vụ ở /manifest.webmanifest và tự gắn <link rel="manifest">.
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Vyra — Tạo mọi loại video bằng AI",
    short_name: "Vyra",
    description:
      "Quảng cáo, KOL, bắt trend, phim ngắn — dựng video 60 giây với giọng Việt thật.",
    start_url: "/app",
    display: "standalone",
    background_color: "#06070D",
    theme_color: "#06070D",
    lang: "vi",
    icons: [{ src: "/icon.svg", type: "image/svg+xml", sizes: "any", purpose: "any" }],
  };
}
