"""Thư viện giọng đọc Việt (persona) — danh mục giọng có cá tính, người dùng chọn để nghe thử.

Trung thực về công nghệ: edge-tts chỉ có 2 giọng neural tiếng Việt (HoaiMy nữ, NamMinh nam).
Mỗi persona là một BIẾN THỂ PHONG CÁCH dựng trên 2 giọng gốc qua prosody (nhịp đọc + cao độ) —
trẻ trung/nhẹ nhàng/trầm ấm/dí dỏm… nghe khác nhau rõ rệt, KHÔNG phải claim giọng vùng miền mà
engine chưa làm được. Khi nối TTS cao cấp (Vbee/VieNeu có giọng vùng), danh mục mở rộng tự nhiên.

Pure data + resolver → dùng chung cho nghe thử (voice.py) và lưu lựa chọn vào job.
"""

from __future__ import annotations

_BASE = {"female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural"}

# rate/pitch là OFFSET so với giọng gốc (edge-tts: rate %, pitch Hz, đều số nguyên).
VOICE_PERSONAS: list[dict] = [
    {"id": "mai", "name": "Mai", "gender": "female", "vibe": "Trẻ trung, năng động",
     "blurb": "Giọng nữ tươi, bắt tai — hợp bán hàng TikTok, thời trang, phụ kiện.",
     "rate": 8, "pitch": 2},
    {"id": "linh", "name": "Linh", "gender": "female", "vibe": "Nhẹ nhàng, tâm tình",
     "blurb": "Êm, gần gũi — hợp skincare, mẹ & bé, sản phẩm chăm sóc.",
     "rate": -4, "pitch": 0},
    {"id": "trang", "name": "Trang", "gender": "female", "vibe": "Rõ ràng, chuyên nghiệp",
     "blurb": "Chững chạc, mạch lạc — hợp review công nghệ, gia dụng, B2B.",
     "rate": 0, "pitch": -1},
    {"id": "bong", "name": "Bống", "gender": "female", "vibe": "Láu lỉnh, dí dỏm",
     "blurb": "Lém lỉnh, vui — hợp đồ ăn vặt, đồ chơi, content Gen Z.",
     "rate": 12, "pitch": 3},
    {"id": "khoa", "name": "Khoa", "gender": "male", "vibe": "Năng động, cuốn hút",
     "blurb": "Giọng nam khoẻ, lôi cuốn — hợp đồ thể thao, gadget, ô tô xe máy.",
     "rate": 8, "pitch": 1},
    {"id": "hung", "name": "Hùng", "gender": "male", "vibe": "Trầm ấm, tin cậy",
     "blurb": "Ấm, chắc chắn — hợp công nghệ, tài chính, sản phẩm cao cấp.",
     "rate": -3, "pitch": -2},
    {"id": "tu", "name": "Tú", "gender": "male", "vibe": "Trẻ trung, vui vẻ",
     "blurb": "Nam trẻ, thân thiện — hợp đồ sinh viên, phụ kiện, content đời thường.",
     "rate": 10, "pitch": 2},
]

_BY_ID = {p["id"]: p for p in VOICE_PERSONAS}


def get_persona(persona_id: str) -> dict | None:
    return _BY_ID.get((persona_id or "").strip().lower())


def resolve(persona_id: str = "", gender: str = "female") -> tuple[str, str, str]:
    """persona_id (ưu tiên) hoặc gender → (voice, rate_str, pitch_str) cho edge-tts.

    Không khớp persona → rơi về giọng gốc theo gender (rate/pitch = 0).
    """
    p = get_persona(persona_id)
    if p is not None:
        voice = _BASE.get(p["gender"], _BASE["female"])
        return voice, f"{int(p['rate']):+d}%", f"{int(p['pitch']):+d}Hz"
    voice = _BASE.get(gender if gender in _BASE else "female")
    return voice, "+0%", "+0Hz"
