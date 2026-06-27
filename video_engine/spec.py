"""JobSpec / RenderResult — hợp đồng stateless cho render-service (M0).

Engine KHÔNG đọc DB. app_api (sau này) đọc DB → dựng JobSpec → gọi render(spec, sink).
JobSpec.to_snapshot() trả về ĐÚNG dict shape mà orchestration cũ (run_job) mong đợi,
để tái dùng tối đa logic stage đã chạy thật.

Map 1-1 từ `pipeline._load_snapshot` (product_dict / kol_dict / snapshot).
3 chỗ pipeline cũ ĐỌC DB trong stage (ScenePreset, PromptTemplate, formula_bank) được
app_api resolve trước và nhét vào JobSpec.scene_prompt / structure_reference / params.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class ProductSpec:
    """Sản phẩm — map từ product_dict (pipeline._load_snapshot)."""
    id: int | None = None
    name: str = ""
    category: str = ""
    price: str = ""                 # đã format sẵn, vd "199,000 VND" (format chuyển sang app_api)
    description: str = ""
    image_path: str = ""
    image_paths_json: str = "[]"
    image_url: str = ""
    rating: float = 0.0
    rating_count: int = 0
    sales_volume: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class KolSpec:
    """KOL persona — map từ kol_dict. None khi job không gắn KOL."""
    id: int | None = None
    name: str = ""
    gender: str = ""
    style: str = ""
    character_sheet: str = ""
    image_path: str = ""
    voice_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class JobSpec:
    """Đầu vào DUY NHẤT của engine. Không tham chiếu DB."""
    job_ref: str                    # id để log/đặt tên asset (KHÔNG phải DB pk)
    mode: str = "product_ad"        # product_ad|premium|kol_full|long_narrative|film_recap
    purpose: str = "final"          # final|draft
    seconds: int = 15
    resolution: str = "720p"
    format_key: str = ""
    format_label: str = ""          # nếu rỗng → engine tự resolve qua get_format(format_key)
    format_prompt: str = ""         # nếu rỗng → engine dùng fallback
    overlay_policy: str = "allow"

    product: ProductSpec = field(default_factory=ProductSpec)
    kol: KolSpec | None = None

    # params free-form: brief, voice{engine,gender,tone}, voice_id, voice_gender, scene_key,
    # template_id, video_prompt, narration_override, music_audio_path, clean_clip, voiceover_off,
    # piapi_task_id, source, video_engine, video_ref_url, ...
    params: dict = field(default_factory=dict)

    # 3 chỗ pipeline cũ đọc DB trong stage → app_api resolve trước, nhét vào đây:
    scene_prompt: str = ""          # = ScenePreset.image_prompt (KOL Studio bối cảnh)
    structure_reference: str = ""   # = PromptTemplate.prompt_vi/en (template đã chọn)

    workdir: str = ""               # thư mục tạm worker tạo (chứa clip/ảnh/voice/final)

    def to_snapshot(self) -> dict:
        """Trả ĐÚNG dict shape `_load_snapshot` cũ → orchestration tái dùng nguyên."""
        from video_engine.formats import get_format

        fmt = get_format(self.format_key) if self.format_key else None
        label = self.format_label or (fmt.label if fmt else (self.format_key or "B-roll sản phẩm"))
        prompt = self.format_prompt or (
            fmt.director_system_prompt if (fmt and fmt.director_system_prompt) else _fallback_prompt()
        )
        policy = self.overlay_policy or (
            (getattr(fmt, "overlay_policy", "") or "allow") if fmt else "allow"
        )
        return {
            "mode": self.mode,
            "purpose": self.purpose,
            "seconds": self.seconds,
            "resolution": self.resolution,
            "params": dict(self.params),
            "product": self.product.to_dict(),
            "kol": self.kol.to_dict() if self.kol else None,
            "format_key": self.format_key,
            "overlay_policy": policy,
            "format_label": label,
            "format_prompt": prompt,
        }

    # ── (de)serialize cho runner_cli + Arq payload ───────────────────────
    @classmethod
    def from_dict(cls, d: dict) -> "JobSpec":
        d = dict(d)
        prod = d.pop("product", None)
        kol = d.pop("kol", None)
        spec = cls(
            job_ref=str(d.pop("job_ref", "cli")),
            product=ProductSpec(**prod) if prod else ProductSpec(),
            kol=KolSpec(**kol) if kol else None,
            **{k: v for k, v in d.items() if k in cls.__dataclass_fields__},
        )
        return spec

    @classmethod
    def from_json(cls, text: str) -> "JobSpec":
        return cls.from_dict(json.loads(text))

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, ensure_ascii=False, indent=2)


def _fallback_prompt() -> str:
    from video_engine.formats import DEFAULT_FORMATS

    return DEFAULT_FORMATS[-1]["director_system_prompt"]


@dataclass
class RenderResult:
    """Kết quả render — app_api dùng để SETTLE/REFUND ví + ghi videos/job_events."""
    status: str                     # READY|QA_FAIL|WAITING_CONFIG|FAILED|QUEUED_BUDGET
    path: str = ""
    error: str = ""
    cost_usd: float = 0.0
    clips_used: int = 0
    stage_timings: dict = field(default_factory=dict)
    shot_plan: dict | None = None
    qa_report: dict | None = None
    resume_task_id: str = ""        # piapi_task_id — retry không trả tiền i2v 2 lần
    fault_class: str = ""           # system|input — app_api quyết hoàn tiền

    def to_dict(self) -> dict:
        return asdict(self)
