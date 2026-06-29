#!/usr/bin/env bash
# Khởi động poller MB Bank — "mini-SePay" tự host, MIỄN PHÍ.
# Đăng nhập API MB, poll giao dịch tiền-vào mỗi vài giây, POST về backend Vyra
# (/v1/billing/ipn/sepay) → backend đối soát memo VYRA######## + cộng credit + đẩy SSE.
#
# Chuẩn bị 1 lần:
#   py -3.12 -m venv .venv-poller
#   .venv-poller/Scripts/python.exe -m pip install mbbank-lib requests
#   (sửa _mb_creds.txt: điền MB_USERNAME + MB_PASSWORD)
#
# Dùng:  bash run_mb_poller.sh
set -euo pipefail
cd "$(dirname "$0")"

# 1) venv riêng (mbbank-lib chưa hỗ trợ Python 3.14 của backend → cô lập)
if [ -x ".venv-poller/Scripts/python.exe" ]; then
  PY=".venv-poller/Scripts/python.exe"          # Windows
elif [ -x ".venv-poller/bin/python" ]; then
  PY=".venv-poller/bin/python"                   # mac/linux
else
  echo "[poller] CHƯA có .venv-poller. Tạo trước:" >&2
  echo "  py -3.12 -m venv .venv-poller" >&2
  echo "  .venv-poller/Scripts/python.exe -m pip install mbbank-lib requests" >&2
  exit 1
fi

# 2) creds (KHÔNG commit) — token đã set sẵn; bạn chỉ cần điền MB_USERNAME/PASSWORD
if [ ! -f _mb_creds.txt ]; then
  echo "[poller] Thiếu _mb_creds.txt — tạo file rồi điền MB_USERNAME, MB_PASSWORD." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. ./_mb_creds.txt
set +a

if [ -z "${MB_USERNAME:-}" ] || [ -z "${MB_PASSWORD:-}" ]; then
  echo "[poller] Chưa điền MB_USERNAME / MB_PASSWORD trong _mb_creds.txt." >&2
  echo "         KHUYẾN NGHỊ dùng 1 tài khoản MB riêng chỉ để thu tiền nạp." >&2
  exit 1
fi

echo "[poller] khởi động: account=${MB_ACCOUNT:-?} → ${VYRA_BACKEND_URL:-http://127.0.0.1:8099} (mỗi ${MB_POLL_INTERVAL_S:-3}s)"
exec "$PY" scripts/mb_poller.py
