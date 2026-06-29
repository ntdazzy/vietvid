#!/usr/bin/env bash
# Khởi động frontend Vyra (Next.js :3000) ở chế độ dev.
# Dùng:  bash run_web.sh   (hoặc Start-Process để chạy nền độc lập)
cd "$(dirname "$0")/apps/web"
exec node_modules/.bin/next dev -p 3000
