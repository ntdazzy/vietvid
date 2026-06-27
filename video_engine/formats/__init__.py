"""9 format quảng cáo (8 category autovis + B-roll) — mỗi format = 1 system prompt cho Director.

Nguồn chuẩn là code (dễ review/diff); ``ensure_default_formats()`` upsert vào DB để
web đọc và founder chỉnh sửa được về sau (DB thắng khi đã có row).
"""

from __future__ import annotations

from sqlalchemy import select

from core.database import db
from core.logger import logger
from core.models import AdFormat

_COMMON_RULES = (
    "Bạn là đạo diễn video quảng cáo affiliate 9:16 cho thị trường Việt Nam. "
    "Trả về DUY NHẤT một JSON object với các khóa: "
    'storyboard (list các shot {"t":"0-3s","shot":"...","camera":"..."}), '
    "narration (lời thoại tiếng Việt tự nhiên, KHÔNG chứa chỉ đạo cảnh/camera/ngoặc vuông, "
    "tốc độ đọc ~2.3 từ/giây nên tổng số từ ≈ 2.3 × số giây video), "
    "image_prompts (list 1-2 prompt tiếng Anh sinh ảnh, mỗi prompt 3 khối: "
    "[hành động cụ thể] · [bối cảnh] · [góc máy/ánh sáng/phong cách photoreal]), "
    "video_prompt (1 prompt tiếng Anh mô tả chuyển động cho model image-to-video, "
    "giữ NGUYÊN sản phẩm: đúng logo, đúng màu, đúng hình dáng), "
    "cta (lời kêu gọi ngắn ≤10 từ), "
    'text_overlays (list chữ vẽ LOCAL đè lên video sau render '
    '[{"t":2.0,"text":"399K","pos":"top","kind":"price","sent":1}] '
    "— theo quy tắc overlay trong prompt; không có thì trả []). "
    "KỊCH BẢN THEO TÂM-LÝ-MUA-HÀNG (bắt buộc): HOOK ≤2 giây đầu giữ chân → PAIN (chạm nỗi đau/"
    "nhu cầu thật) → PROOF (chứng minh bằng tính năng/chất liệu/cách dùng cụ thể) → KHAN HIẾM/GIÁ "
    "(ưu đãi, số lượng, giá tốt — chỉ dùng số liệu thật được cung cấp) → CTA chốt đơn. "
    "Không phóng đại sai sự thật, chỉ nêu lợi ích có trong mô tả sản phẩm. "
    "AN TOÀN MODERATION (bắt buộc cho prompt ảnh/video): KHÔNG mô tả xịt/thoa/áp sản phẩm "
    "lên da, cổ, cổ tay hay bất kỳ vùng cơ thể nào; KHÔNG cận cảnh vùng da hở. "
    "Hành động an toàn: cầm sản phẩm, nâng lên ngang mặt, mỉm cười với camera, "
    "chỉ vào sản phẩm, đặt xuống bàn, xoay nhẹ sản phẩm."
)

DEFAULT_FORMATS: list[dict] = [
    {
        "key": "ugc_review",
        "label": "UGC chân thực",
        "icon": "smartphone",
        "description": "Người thật cầm sản phẩm review như quay điện thoại — tin cậy, đời thường.",
        "requires_kol": True,
        "supports_product_only": False,
        "default_duration": 15,
        "sort_order": 1,
        "overlay_policy": "require",
        "director_system_prompt": _COMMON_RULES
        + " Format UGC: nhịp nhanh, rung nhẹ kiểu cầm tay, ánh sáng tự nhiên trong nhà, "
        "KOL nói thẳng vào camera như bạn bè khuyên nhau, hook 2 giây đầu phải giữ chân.",
    },
    {
        "key": "unboxing",
        "label": "Unboxing cảm xúc",
        "icon": "package-open",
        "description": "Mở hộp + phản ứng wow + cận chi tiết sản phẩm.",
        "requires_kol": False,
        "supports_product_only": True,
        "default_duration": 12,
        "sort_order": 2,
        "overlay_policy": "require",
        "director_system_prompt": _COMMON_RULES
        + " Format Unboxing: shot 1 mở hộp (cận tay), shot 2 lộ sản phẩm + phản ứng, "
        "shot 3 cận chi tiết chất liệu/logo, kết bằng CTA. Ánh sáng bàn setup ấm.",
    },
    {
        "key": "expert_review",
        "label": "Đánh giá chuyên sâu",
        "icon": "search-check",
        "description": "KOL phân tích ưu điểm chính, giọng chuyên gia đáng tin.",
        "requires_kol": True,
        "supports_product_only": False,
        "default_duration": 15,
        "sort_order": 3,
        "overlay_policy": "allow",
        "director_system_prompt": _COMMON_RULES
        + " Format Đánh giá: nhịp chậm rãi chắc chắn, KOL chỉ vào 2-3 điểm mạnh cụ thể, "
        "có shot cận sản phẩm minh họa từng ý, tone chuyên nghiệp nhưng gần gũi.",
    },
    {
        "key": "tutorial",
        "label": "Hướng dẫn dùng",
        "icon": "list-checks",
        "description": "3 bước dùng sản phẩm — trực quan, dễ làm theo.",
        "requires_kol": False,
        "supports_product_only": True,
        "default_duration": 12,
        "sort_order": 4,
        "overlay_policy": "allow",
        "director_system_prompt": _COMMON_RULES
        + " Format Hướng dẫn: chia đúng 3 bước rõ ràng (bước 1/2/3), mỗi bước 1 shot "
        "hành động cụ thể với sản phẩm, narration đếm bước, kết quả ở shot cuối.",
    },
    {
        "key": "tvc",
        "label": "TVC ngắn",
        "icon": "clapperboard",
        "description": "Quảng cáo bóng bẩy kiểu TVC — sản phẩm là ngôi sao.",
        "requires_kol": False,
        "supports_product_only": True,
        "default_duration": 10,
        "sort_order": 5,
        "overlay_policy": "require",
        "director_system_prompt": _COMMON_RULES
        + " Format TVC: ánh sáng studio cao cấp, chuyển động camera mượt (dolly/orbit), "
        "sản phẩm nổi khối trên nền tối giản, chữ ít, cảm giác premium.",
    },
    {
        "key": "product_broll",
        "label": "B-roll sản phẩm",
        "icon": "film",
        "description": "Sản phẩm xoay/cận cảnh lifestyle — không người, rẻ nhất.",
        "requires_kol": False,
        "supports_product_only": True,
        "default_duration": 10,
        "sort_order": 6,
        "overlay_policy": "allow",
        "director_system_prompt": _COMMON_RULES
        + " Format B-roll: KHÔNG có người, sản phẩm đặt trong bối cảnh đời sống hợp ngách, "
        "chuyển động chậm (xoay nhẹ/pan/cận texture), ánh sáng đẹp tôn chất liệu.",
    },
    # ── 3 format bổ sung cho đủ bộ autovis (học từ docs/autovis_prompts/product_templates.md) ──
    {
        "key": "hyper_motion",
        "label": "Hyper Motion",
        "icon": "zap",
        "description": "Sản phẩm chuyển động cực nhanh/360°, hiệu ứng tốc độ — bắt mắt, viral.",
        "requires_kol": False,
        "supports_product_only": True,
        "default_duration": 10,
        "sort_order": 7,
        "overlay_policy": "allow",
        "director_system_prompt": _COMMON_RULES
        + " Format Hyper Motion: KHÔNG cần người, sản phẩm là tâm điểm — xoay 360°, bay lượn, "
        "hiệu ứng tốc độ/hyperlapse, camera orbit nhanh mượt, nền gradient/khói/ánh sáng động, "
        "nhịp cực nhanh khớp beat nhạc, cảm giác cinematic năng lượng cao.",
    },
    {
        "key": "tryon",
        "label": "Thử đồ ảo",
        "icon": "shirt",
        "description": "Người mẫu mặc thử sản phẩm thời trang, xoay soi gương — cho thời trang/phụ kiện.",
        "requires_kol": True,
        "supports_product_only": False,
        "default_duration": 15,
        "sort_order": 8,
        "overlay_policy": "forbid",
        "director_system_prompt": _COMMON_RULES
        + " Format Thử đồ ảo: nhân vật (tả bằng TEXT trong video_prompt — tuổi/sắc tộc/tóc/dáng) "
        "mặc sản phẩm thời trang, đứng trước gương soi toàn thân, xoay người 2 bên kiểm tra dáng, "
        "chỉnh vai/gấu áo, jump-cut giữa các outfit/góc; TRANG PHỤC (sản phẩm) là tâm điểm, "
        "tả chính xác màu/kiểu/chất liệu. Bối cảnh phòng thay đồ/phòng ngủ tối giản, ánh sáng tự nhiên.",
    },
    {
        "key": "tryon_pro",
        "label": "Thử đồ ảo Pro",
        "icon": "sparkles",
        "description": "Thử đồ chuẩn studio/lookbook chuyên nghiệp — nhiều pose, ánh sáng cao cấp.",
        "requires_kol": True,
        "supports_product_only": False,
        "default_duration": 15,
        "sort_order": 9,
        "overlay_policy": "forbid",
        "director_system_prompt": _COMMON_RULES
        + " Format Thử đồ ảo Pro: như thử đồ nhưng chuẩn LOOKBOOK studio — nhân vật (tả bằng TEXT) "
        "tạo nhiều pose thời trang chuyên nghiệp, chuyển pose mượt, ánh sáng studio cao cấp, "
        "phông nền sạch/editorial, tôn dáng và chi tiết sản phẩm; cảm giác premium như catalogue TMĐT.",
    },
]


def ensure_default_formats() -> None:
    """Upsert format mặc định (chỉ thêm khi thiếu — không ghi đè chỉnh sửa của founder)."""
    with db.transaction() as session:
        existing = set(session.scalars(select(AdFormat.key)).all())
        added = 0
        for spec in DEFAULT_FORMATS:
            if spec["key"] in existing:
                continue
            session.add(AdFormat(**spec))
            added += 1
        if added:
            logger.info(f"[formats] seed {added} format mặc định vào ad_formats")


def get_format(key: str) -> AdFormat | None:
    with db.transaction() as session:
        fmt = session.get(AdFormat, key)
        if fmt is not None:
            session.expunge(fmt)
        return fmt
