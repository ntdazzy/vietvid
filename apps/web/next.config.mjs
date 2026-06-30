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
  // Proxy API về backend local → khi API_BASE_URL rỗng, trình duyệt gọi same-origin
  // /v1/* và Next chuyển tiếp về :8099. Cho phép chạy sau MỘT tunnel/proxy duy nhất.
  async rewrites() {
    return [
      { source: "/v1/:path*", destination: "http://127.0.0.1:8099/v1/:path*" },
      { source: "/api/v1/:path*", destination: "http://127.0.0.1:8099/api/v1/:path*" },
    ];
  },
};

export default withNextIntl(nextConfig);
