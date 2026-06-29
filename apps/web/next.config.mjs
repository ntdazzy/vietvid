import createNextIntlPlugin from "next-intl/plugin";

// Bật next-intl ở server (getTranslations) — đọc cấu hình request từ file này.
const withNextIntl = createNextIntlPlugin("./src/lib/i18n/request.ts");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Cho phép phát video/ảnh từ backend (job video, R2 sau này).
  images: {
    // Ưu tiên AVIF/WebP cho mọi <Image> (nhẹ hơn JPEG/PNG đáng kể).
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      { protocol: "http", hostname: "127.0.0.1" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
};

export default withNextIntl(nextConfig);
