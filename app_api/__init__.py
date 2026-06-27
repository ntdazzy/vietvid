"""VietVid app_api — lớp SaaS đa-tenant (auth · tenancy · wallet · billing · jobs).

Đứng trên engine stateless (video_engine.render_service.render). app_api đọc DB → dựng
JobSpec → enqueue → engine render → SETTLE/REFUND ví. Engine KHÔNG biết tenant/tiền.
"""
