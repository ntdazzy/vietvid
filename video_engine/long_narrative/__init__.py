"""Engine long_narrative — video YouTube news-entertainment dài (16:9, multi-voice).

Tách nhánh từ `video_engine.pipeline.run_job()` khi `mode == "long_narrative"` (xem
`docs/PLAN-video-engine-1.2.md`). Early-branch chèn TRƯỚC reserve để KHÔNG dùng estimator
Seedance/giây. **KHÔNG đụng** path Seedance/product/KOL đang kiếm tiền — chỉ THÊM nhánh.
"""

from video_engine.long_narrative.script_schema import (
    VALID_CONTEXTS,
    VALID_IMAGE_SOURCES,
    Beat,
    LongformScript,
    NarrationBlock,
)

__all__ = [
    "LongformScript",
    "Beat",
    "NarrationBlock",
    "VALID_CONTEXTS",
    "VALID_IMAGE_SOURCES",
]
