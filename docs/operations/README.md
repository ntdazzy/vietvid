# OPERATIONS_AND_ECONOMICS — Sổ tay vận hành Vyra

Bộ tài liệu vận hành Vyra **như một công ty**: hạ tầng, dữ liệu, tiền, admin, bảo trì, quốc tế hoá, lộ trình. Mỗi chủ đề một file để dễ sửa/bảo trì. Viết kiểu "cầm tay chỉ việc", bám code thật.

> Nguồn-sự-thật định vị/roadmap sản phẩm: [../VISION.md](../VISION.md). Ngữ cảnh kỹ thuật tổng: [../HANDOFF.md](../HANDOFF.md). Schema M2+: [designs/SYSTEM_DESIGN.md](../designs/SYSTEM_DESIGN.md). Nâng cấp UI: [../UI-UPGRADE-BLUEPRINT.md](../UI-UPGRADE-BLUEPRINT.md).

## Cách đọc
Bắt đầu ở **[00-overview](00-overview.md)** (bức tranh + glossary), rồi đọc theo nhóm bên dưới. Khi triển khai, theo **[20-roadmap](20-roadmap.md)** (A-Z theo pha).

**Trạng thái:** ✅ đã có · ⚙️ một phần · 🔜 chưa làm.

## Mục lục

### Tổng quan
- [00-overview](00-overview.md) — Vyra như một công ty: mô hình, sơ đồ các mảnh, nguyên tắc, glossary
- [01-architecture](01-architecture.md) — kiến trúc + luồng tạo video end-to-end + bản đồ điều tra lỗi

### Hạ tầng
- [02-infrastructure](02-infrastructure.md) — hosting (Vercel/Railway/Neon/Upstash/R2), env, chi phí, dựng từ số 0
- [03-database](03-database.md) — Postgres + RLS fail-closed, migrations, backup/PITR/restore
- [04-storage-media](04-storage-media.md) — Cloudflare R2, signed URL, GC theo expires_at
- [05-queue-worker-rendering](05-queue-worker-rendering.md) — Arq+Redis, vòng đời job, retry/idempotency
- [06-providers](06-providers.md) — video/ảnh/giọng (PiAPI/fal/Vbee), router, fallback, ToS

### Kinh tế & tiền
- [07-economics](07-economics.md) — đơn vị kinh tế: giá vốn/video, biên, cách đo thật
- [08-pricing-plans-credits](08-pricing-plans-credits.md) — giá credit, gói, markup model
- [09-free-tier-abuse](09-free-tier-abuse.md) — siết free tier + chống lạm dụng
- [10-payments](10-payments.md) — VN (MoMo/VietQR/SePay) + quốc tế (Stripe/Visa), IPN, hoá đơn
- [21-financial-model](21-financial-model.md) — P&L, điểm hoà vốn, 3 kịch bản

### Vận hành
- [11-admin-panel](11-admin-panel.md) — đặc tả web admin (tra cứu/credit/suspend/monitor/maintenance)
- [12-logging-observability](12-logging-observability.md) — log + Sentry + request-id (để Claude debug)
- [13-monitoring-uptime](13-monitoring-uptime.md) — health-check, UptimeRobot, alert, SLO
- [14-backup-dr-maintenance](14-backup-dr-maintenance.md) — backup/DR, maintenance mode, rollback
- [15-security](15-security.md) — secret, auth, RLS, PII, rate limit
- [18-runbooks](18-runbooks.md) — sổ tay xử lý sự cố (job kẹt, tiền không cộng, DB chậm...)
- [19-support](19-support.md) — luồng hỗ trợ user (solo + Claude)

### Quốc tế
- [16-i18n](16-i18n.md) — next-intl + /[locale] + tự nhận theo IP + nội dung theo vùng

### Triển khai
- [17-deployment-cicd](17-deployment-cicd.md) — deploy Railway/Vercel, migration, rollback, go-live
- [20-roadmap](20-roadmap.md) — lộ trình A-Z theo pha

## Quyết định lớn còn MỞ (cần chủ dự án chốt / đo thật)
1. **Hosting**: Railway all-in-one (web+api+worker+Postgres+Redis) hay tách Vercel (web) + Railway (api). → [02](02-infrastructure.md), [17](17-deployment-cicd.md).
2. **Đo chi phí render thật/video** sau khi cắm key prod (PiAPI/fal + Vbee) → điền [07-economics](07-economics.md), [21-financial-model](21-financial-model.md).
3. **ToS gói API thương mại** (Vbee/PiAPI/fal) có cho phép phục vụ end-user không → [06](06-providers.md), [08](08-pricing-plans-credits.md).
4. **Admin**: hiện gated bằng **email allowlist** (`VIETVID_ADMIN_EMAILS`), KHÔNG phải role-trong-DB. Đủ cho 1 founder-admin; nếu cần admin đa cấp/đa-org sau này mới thêm role. → [11-admin-panel](11-admin-panel.md), [15-security](15-security.md).

## Checklist tổng (high-level)
- [ ] Chốt hosting + dựng prod (02, 17)
- [ ] Bật queue mode + R2 + GC (05, 04)
- [ ] Cắm key render thật + đo chi phí/video (06, 07)
- [ ] Định giá credit/gói + siết free tier (08, 09)
- [ ] Bật payments go-live + đối soát (10)
- [ ] Admin + logging + monitoring + backup (11–14)
- [ ] i18n + quốc tế (16)
- [ ] Theo lộ trình pha (20)
