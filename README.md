# VietVid — SaaS tạo video AI giọng Việt

SaaS đa-tenant biến ảnh/mô tả sản phẩm thành video review giọng Việt thật, giá minh bạch.
Engine tái dùng từ `affiliatebot/video_engine`, đóng gói thành render-service stateless.

Thiết kế chi tiết: `~/.claude/plans/glimmering-leaping-sutton.md`.

## Cấu trúc

```
apps/web        # Next.js (frontend B)
apps/admin      # trang admin (M3)
services/app_api # FastAPI đa-tenant: auth · tenancy · wallet(ACID) · billing · jobs
services/engine  # render-service stateless (copy từ video_engine): render(spec) -> RenderResult
config           # registry pattern (1 dòng/key → settings + .env + credential center)
alembic          # migrations Postgres
infra            # docker-compose (postgres/redis/minio)
```

## Lộ trình

- **M0** Engine-service stateless — `python -m services.engine.runner_cli <jobspec.json>` ra MP4, không cần DB.
- **M1** Auth + ví credit ACID + 1 luồng review + VNPay + Arq.
- **M2** KOL Studio + nhiều loại video + Momo.
- **M3** Auto-post + admin + moderation.
- **M4** Mobile (Flutter). **M5** Public API / white-label.

## M0 — chạy thử

```bash
python -m services.engine.runner_cli services/engine/sample_jobspec.json
```
