#!/usr/bin/env bash
# Khởi động backend Vyra (:8099) với ĐỦ env trong 1 lệnh.
#   - 51 render-provider key (GEMINI/PIAPI/VBEE/...) nạp từ .env
#   - DB + admin + master key mã hoá secret cấu hình
# Bank / MoMo / VNPay / webhook-token: KHÔNG cắm env nữa → cấu hình qua màn admin
#   (/app/admin → "Phương thức thanh toán"), lưu DB, secret mã hoá tại chỗ.
#
# Dùng:  bash run_backend.sh
cd "$(dirname "$0")"

# 1) Render provider keys từ .env (export hết)
set -a
# shellcheck disable=SC1091
[ -f .env ] && . ./.env 2>/dev/null || true
set +a

# 2) Cấu hình lõi
export VIETVID_DATABASE_URL="$(cat _vietvid_db_url.txt)"
export VIETVID_ADMIN_EMAILS="admin@vyra.local"

# 3) Master key mã hoá secret cấu hình thanh toán — TẠO 1 LẦN, GIỮ CỐ ĐỊNH.
#    (Đổi key = mọi secret đã lưu trong DB sẽ không giải mã được nữa.)
if [ ! -f _vietvid_config_secret.txt ]; then
  head -c 32 /dev/urandom | base64 | tr -d '\n' > _vietvid_config_secret.txt
  echo "[run] đã tạo master key mã hoá -> _vietvid_config_secret.txt (giữ bí mật, KHÔNG commit)"
fi
export VIETVID_CONFIG_SECRET="$(cat _vietvid_config_secret.txt)"

echo "[run] khởi động uvicorn :8099 (đủ env: render keys + DB + admin + config-secret)"
exec python -m uvicorn app_api.main:app --host 127.0.0.1 --port 8099 --log-level warning
