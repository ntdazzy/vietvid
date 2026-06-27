"""Schema kịch bản V2 cho engine long_narrative (video YouTube news-entertainment).

Khác narration text PHẲNG (prototype make_video15 / beats15_clean.json): mỗi beat có
`narration_blocks[]` với `speaker` + `context` để bật multi-voice nhập vai + nhạc/ducking/SFX
theo cảm xúc. **Back-compat:** file phẳng `{label,callout,narration,img_prompt}` tự được bọc
thành 1 block `speaker="narrator"` nên dữ liệu cũ (beats15_clean.json) vẫn load chạy.

Đọc là làm đúng:
- `context ∈ {normal,hype,joke,climax,whisper,drama}` → audio.py quyết nhạc/ducking/mute,
  visual.py quyết biến thể biểu cảm + nhịp.
- `image_source ∈ {ai,news,stock}` → visual.py ưu tiên ảnh tư liệu > stock > AI.
- `narration_text` = ghép text mọi block → feed ASR/QA (check_voice coverage) + foley keyword scan.
- `cache_key()` = hash ổn định để render incremental (sửa beat nào re-render beat đó).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any

VALID_CONTEXTS = {"normal", "hype", "joke", "climax", "whisper", "drama"}
VALID_IMAGE_SOURCES = {"ai", "news", "stock"}
DEFAULT_SPEAKER = "narrator"
DEFAULT_CONTEXT = "normal"


def _norm_context(value: Any, fallback: str = DEFAULT_CONTEXT) -> str:
    v = str(value or "").strip().lower()
    return v if v in VALID_CONTEXTS else fallback


@dataclass
class NarrationBlock:
    """1 lượt thoại: 1 speaker đọc NGUYÊN VĂN `text` trong 1 call TTS (không chẻ câu)."""

    speaker: str = DEFAULT_SPEAKER
    text: str = ""
    context: str = DEFAULT_CONTEXT

    @classmethod
    def from_any(cls, raw: Any, beat_context: str = DEFAULT_CONTEXT) -> "NarrationBlock":
        if isinstance(raw, str):
            return cls(speaker=DEFAULT_SPEAKER, text=raw.strip(), context=beat_context)
        speaker = str(raw.get("speaker") or DEFAULT_SPEAKER).strip() or DEFAULT_SPEAKER
        text = str(raw.get("text") or "").strip()
        context = _norm_context(raw.get("context"), beat_context)
        return cls(speaker=speaker, text=text, context=context)

    def to_dict(self) -> dict:
        return {"speaker": self.speaker, "text": self.text, "context": self.context}


@dataclass
class Beat:
    """1 nhịp kể: 1 callout + 1 nguồn ảnh + chuỗi narration_blocks (1 hoặc nhiều speaker)."""

    label: str = ""
    callout: str = ""
    img_prompt: str = ""
    context: str = DEFAULT_CONTEXT          # context mặc định của beat (block không set thì kế thừa)
    image_source: str = "ai"               # ai | news | stock
    narration_blocks: list[NarrationBlock] = field(default_factory=list)
    broll_keywords: list[str] = field(default_factory=list)
    photo_subject: str = ""                 # mode photo_meme: entity để lấy ẢNH THẬT (tên cầu thủ/CLB/sự kiện)
    meme_tags: list[str] = field(default_factory=list)   # mode photo_meme: nhãn cảm xúc/cà-khịa để khớp meme
    sfx_hint: str = ""
    beat_id: int | None = None

    @property
    def narration_text(self) -> str:
        return " ".join(b.text for b in self.narration_blocks if b.text).strip()

    @property
    def speakers(self) -> list[str]:
        out: list[str] = []
        for b in self.narration_blocks:
            if b.speaker not in out:
                out.append(b.speaker)
        return out

    @property
    def is_multivoice(self) -> bool:
        return len(self.speakers) > 1

    @classmethod
    def from_dict(cls, raw: dict, idx: int | None = None) -> "Beat":
        context = _norm_context(raw.get("context"))
        image_source = str(raw.get("image_source") or "ai").strip().lower()
        if image_source not in VALID_IMAGE_SOURCES:
            image_source = "ai"
        blocks_raw = raw.get("narration_blocks")
        if blocks_raw:
            blocks = [NarrationBlock.from_any(b, context) for b in blocks_raw]
        else:
            # back-compat: narration text phẳng → 1 block narrator
            flat = str(raw.get("narration") or "").strip()
            blocks = [NarrationBlock(DEFAULT_SPEAKER, flat, context)] if flat else []
        blocks = [b for b in blocks if b.text]
        broll = [str(k).strip() for k in (raw.get("broll_keywords") or []) if str(k).strip()]
        meme_tags = [str(k).strip() for k in (raw.get("meme_tags") or []) if str(k).strip()]
        beat_id = raw.get("beat_id")
        if beat_id is None:
            beat_id = idx
        return cls(
            label=str(raw.get("label") or "").strip(),
            callout=str(raw.get("callout") or "").strip(),
            img_prompt=str(raw.get("img_prompt") or "").strip(),
            context=context,
            image_source=image_source,
            narration_blocks=blocks,
            broll_keywords=broll,
            photo_subject=str(raw.get("photo_subject") or "").strip(),
            meme_tags=meme_tags,
            sfx_hint=str(raw.get("sfx_hint") or "").strip(),
            beat_id=beat_id,
        )

    def to_dict(self) -> dict:
        return {
            "beat_id": self.beat_id,
            "label": self.label,
            "callout": self.callout,
            "context": self.context,
            "image_source": self.image_source,
            "img_prompt": self.img_prompt,
            "narration_blocks": [b.to_dict() for b in self.narration_blocks],
            "broll_keywords": self.broll_keywords,
            "photo_subject": self.photo_subject,
            "meme_tags": self.meme_tags,
            "sfx_hint": self.sfx_hint,
        }

    def cache_key(self, voice_map: dict[str, str] | None = None) -> str:
        """Hash ổn định cho render incremental: đổi nội dung/giọng beat → đổi key → re-render."""
        payload = {
            "blocks": [(b.speaker, b.text, b.context) for b in self.narration_blocks],
            "img_prompt": self.img_prompt,
            "context": self.context,
            "image_source": self.image_source,
            "broll": self.broll_keywords,
            "photo_subject": self.photo_subject,
            "meme_tags": self.meme_tags,
            "sfx": self.sfx_hint,
            "voices": {s: (voice_map or {}).get(s, "") for s in self.speakers},
        }
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(blob.encode("utf-8")).hexdigest()


@dataclass
class LongformScript:
    title: str = ""
    beats: list[Beat] = field(default_factory=list)
    category: str = "football"
    meta: dict = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj: Any) -> "LongformScript":
        # back-compat: file gốc là LIST beat phẳng (beats15_clean.json)
        if isinstance(obj, list):
            beats = [Beat.from_dict(b, i) for i, b in enumerate(obj)]
            return cls(title="", beats=beats)
        title = str(obj.get("title") or "").strip()
        category = str(obj.get("category") or "football").strip()
        raw_beats = obj.get("beats") or []
        beats = [Beat.from_dict(b, i) for i, b in enumerate(raw_beats)]
        meta = {k: v for k, v in obj.items() if k not in {"title", "beats", "category"}}
        return cls(title=title, beats=beats, category=category, meta=meta)

    @classmethod
    def from_file(cls, path: str) -> "LongformScript":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_obj(json.load(f))

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "category": self.category,
            **self.meta,
            "beats": [b.to_dict() for b in self.beats],
        }

    def to_file(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @property
    def full_narration(self) -> str:
        return " ".join(b.narration_text for b in self.beats if b.narration_text).strip()

    @property
    def total_chars(self) -> int:
        return sum(len(b.narration_text) for b in self.beats)
