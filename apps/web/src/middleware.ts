import { NextRequest, NextResponse } from "next/server";
import { LOCALE_COOKIE } from "@/lib/i18n/config";
import { AUTH_COOKIE } from "@/lib/config";

// Middleware NHẸ — chỉ thao tác header/cookie, KHÔNG gọi DB/API, không async nặng.
//
// Trách nhiệm:
//   1. i18n geo: nếu request chưa có cookie NEXT_LOCALE, đoán locale theo quốc gia
//      (VN -> vi, còn lại -> en) và set cookie. Tôn trọng lựa chọn tay (đã có cookie).
//   2. Security headers cơ bản cho mọi response.
//
//   3. Auth-guard CHỈ màn TẠO (/app/create): xem mọi màn /app/* tự do, chỉ khi
//      vào trình tạo (tốn credit) mới cần đăng nhập. Thiếu cookie cờ phiên
//      (vyra_auth) -> redirect /login. Cookie chỉ là CỜ "có phiên" (không chứa
//      token); token thật ở localStorage, API mới là cổng bảo mật thật. AuthGate
//      client (create/layout) giữ làm lớp 2. Login set cookie, logout xoá.

const SECURITY_HEADERS: Record<string, string> = {
  "X-Frame-Options": "SAMEORIGIN",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  // Permissions-Policy cơ bản: tắt các quyền nhạy cảm theo mặc định.
  "Permissions-Policy": "camera=(), microphone=(), geolocation=(), browsing-topics=()",
  // TODO(csp): Content-Security-Policy CỐ TÌNH chưa bật cứng — CSP chặt dễ vỡ
  // (Next inline scripts, ảnh/CDN bên thứ ba, nonce per-request). Bật sau khi
  // audit kỹ nguồn tài nguyên + thêm nonce, tránh trắng trang production.
};

export function middleware(request: NextRequest) {
  // (3) Auth-guard: CHỈ chặn màn TẠO (/app/create) khi chưa có cookie cờ phiên
  //     -> /login (kèm ?next để quay lại). Các màn /app/* khác xem tự do.
  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/app/create") && !request.cookies.has(AUTH_COOKIE)) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  const response = NextResponse.next();

  // (2) Security headers cho mọi response.
  for (const [key, value] of Object.entries(SECURITY_HEADERS)) {
    response.headers.set(key, value);
  }

  // (1) i18n geo — chỉ set khi CHƯA có cookie (tôn trọng lựa chọn tay qua switcher).
  const hasLocaleCookie = request.cookies.has(LOCALE_COOKIE);
  if (!hasLocaleCookie) {
    const country =
      request.headers.get("x-vercel-ip-country") ||
      request.headers.get("cf-ipcountry") ||
      "";
    // Không có geo (localhost/proxy) HOẶC VN -> vi (thị trường chính). Nước khác -> en.
    const locale = !country || country.toUpperCase() === "VN" ? "vi" : "en";

    response.cookies.set(LOCALE_COOKIE, locale, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365, // 1 năm
      sameSite: "lax",
    });
  }

  return response;
}

export const config = {
  // Áp cho mọi route TRỪ tài nguyên tĩnh của Next, favicon, và file có đuôi
  // (ảnh, font, .txt...). Tránh chạy middleware thừa trên asset.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)",
  ],
};
