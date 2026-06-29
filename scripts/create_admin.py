"""Tạo/đảm bảo tài khoản ADMIN cho Vyra.

CƠ CHẾ: admin KHÔNG phải role-trong-DB. Admin = email nằm trong biến môi trường
`VIETVID_ADMIN_EMAILS` (đọc lúc backend khởi động). `/v1/auth/me` trả is_admin=true
khi email người đăng nhập nằm trong allowlist → frontend hiện mục "Quản trị".

Script này tạo USER trong DB (qua /v1/auth/register, idempotent: 409 = đã có), rồi
in hướng dẫn thêm email vào allowlist + restart backend.

Dùng:
  PYTHONUTF8=1 /c/Python314/python -m scripts.create_admin [email] [password] [api_base]
Mặc định: admin@vyra.local / Admin@12345 / http://127.0.0.1:8099
"""

from __future__ import annotations

import sys

import httpx

EMAIL = (sys.argv[1] if len(sys.argv) > 1 else "admin@vyra.local").strip().lower()
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "Admin@12345"
API = (sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8099").rstrip("/")


def main() -> None:
    with httpx.Client(timeout=30) as c:
        r = c.post(
            f"{API}/v1/auth/register",
            json={"email": EMAIL, "password": PASSWORD, "full_name": "Vyra Admin"},
        )
        if r.status_code == 201:
            print(f"✓ Đã tạo tài khoản: {EMAIL}")
        elif r.status_code == 409:
            print(f"• Tài khoản đã tồn tại: {EMAIL} (ok, dùng tiếp)")
        elif r.status_code == 404:
            print("✗ register tắt (auth_mode=supabase?). Đăng ký qua Supabase rồi thêm email vào allowlist.")
            return
        else:
            print(f"✗ Lỗi {r.status_code}: {r.text[:300]}")
            return

    print()
    print("=== ĐỂ TÀI KHOẢN NÀY THÀNH ADMIN (login thấy mục 'Quản trị') ===")
    print(f"  1. Khi chạy backend, set:  VIETVID_ADMIN_EMAILS={EMAIL}")
    print("     (nhiều admin: ngăn cách bằng dấu phẩy)")
    print("  2. Restart backend (NHỚ kèm VIETVID_DATABASE_URL).")
    print(f"  3. Đăng nhập {EMAIL} / (mật khẩu đã đặt) → nav hiện 'Quản trị' → /app/admin")
    print()
    print(f"  Kiểm chứng: GET {API}/v1/auth/me (Bearer token) → is_admin=true")


if __name__ == "__main__":
    main()
