"""Text cleanup before TTS.

Scripts may contain visual directions in brackets, product codes, or compact
measurements that sound bad when read literally. Keep this layer small and
deterministic so audio is safer without changing script semantics.
"""

from __future__ import annotations

import re

_BRACKETED_RE = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]\s*")
_MULTISPACE_RE = re.compile(r"\s+")
_PRODUCT_CODE_RE = re.compile(r"\b([A-Z])([0-9]{1,3})([A-Z]?)\b")
_SIZE_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)\s*(cm|mm|m)\b", re.I)
_NUMBER_UNIT_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(cm|mm|m|kg|g|w|mah|ml|l)\b", re.I)

_LETTER_READINGS = {
    "A": "A",
    "B": "Bê",
    "C": "Cê",
    "D": "Dê",
    "E": "E",
    "F": "Ép",
    "G": "Gờ",
    "H": "Hát",
    "I": "I",
    "J": "Giây",
    "K": "Ca",
    "L": "En",
    "M": "Em",
    "N": "En",
    "O": "Ô",
    "P": "Pê",
    "Q": "Quy",
    "R": "Rờ",
    "S": "Ét",
    "T": "Tê",
    "U": "U",
    "V": "Vê",
    "W": "Đúp bờ vê",
    "X": "Ích",
    "Y": "Y",
    "Z": "Dét",
}

_WORD_REPLACEMENTS = {
    "turbo": "tua bô",
    "type-c": "tai xì",
    "type c": "tai xì",
    "usb": "u ét bê",
    "mini": "mini",
}

# Tên riêng nước ngoài (bóng đá / tin tức) Vbee đọc sai → phiên âm gần đúng tiếng Việt
# (syllable cách nhau bằng KHOẢNG TRẮNG, không gạch nối — Vbee đọc liền mạch hơn).
# Cụm nhiều từ đặt TRƯỚC từ đơn để khớp cụm trước. Áp dụng whole-word, case-insensitive.
# Mở rộng dần khi gặp tên mới; KHÔNG viết engine mới (dùng chung _replace_words).
_NAME_READINGS = {
    "World Cup": "Quơ Cắp",
    "Mac Allister": "Mác A li xtơ",
    "Nico Gonzalez": "Ni cô Gôn da lét",
    "Roger Milla": "Rô giơ Mi la",
    "Lionel Messi": "Li ô neo Mét xi",
    "Messi": "Mét xi",
    "Klose": "Klô dơ",
    "Zidane": "Zi đan",
    "Argentina": "Ác hen ti na",
    "Algeria": "An giê ri",
    "Penalty": "Pê nan ti",
    "Lautaro": "Lau ta rô",
    "Chaibi": "Chai bi",
    "Miroslav": "Mi rô xláp",
    "Ronaldo": "Rô nan đô",
    "Cameroon": "Ca mơ run",
    "Milla": "Mi la",
    "Pelé": "Pê lê",
    "Pele": "Pê lê",
    "Jordan": "Gioóc đan",
    "Arrowhead": "A rô hét",
    "Kansas": "Can dát",
    "Uganda": "U gan đa",
    "Brazil": "Bra din",
    "Luca": "Lu ca",
}

# Slang/từ tiếng Anh hay gặp trong recap → phiên âm tiếng Việt (TTS đọc nguyên xi sẽ sai bét, vd
# GOAT → "gấu hoa tịt"). GOAT xử RIÊNG (chỉ chữ HOA → 'gốt'; 'goat' thường = con dê, GIỮ nguyên).
_SLANG_READINGS = {
    "aura farming": "ô ra phơ ming",
    "aura farmer": "ô ra phơ mơ",
    "aura": "ô ra",
    "fanpage": "phen pây",
    "fan": "phen",
    "drama": "đờ ra ma",
    "troll": "trôn",
    "meme": "mim",
    "highlight": "hai lai",
    "check var": "chếch va",
    "clip": "cờ líp",
    "trend": "tren",
    "combo": "com bô",
    "level": "lê vồ",
}


def apply_slang_readings(text: str) -> str:
    """Phiên âm slang tiếng Anh → tiếng Việt cho TTS. DÙNG CHUNG đường Vbee (qua normalize_tts_text) +
    Gemini (gọi riêng trong _clean_for_gemini). GOAT chỉ khớp CHỮ HOA (goat thường = con dê)."""
    out = text or ""
    out = re.sub(r"\bGOAT\b", "gốt", out)                       # CHỈ chữ hoa (không re.I)
    for source, target in _SLANG_READINGS.items():
        out = re.sub(rf"\b{re.escape(source)}\b", target, out, flags=re.I)
    return out


_UNIT_READINGS = {
    "cm": "xăng ti mét",
    "mm": "mi li mét",
    "m": "mét",
    "kg": "ki lô gam",
    "g": "gam",
    "w": "oát",
    "mah": "mi li am pe giờ",
    "ml": "mi li lít",
    "l": "lít",
}


def normalize_tts_text(text: str) -> str:
    cleaned = strip_stage_directions(text)
    cleaned = _SIZE_RE.sub(_replace_size, cleaned)
    cleaned = _NUMBER_UNIT_RE.sub(_replace_number_unit, cleaned)
    cleaned = _PRODUCT_CODE_RE.sub(_replace_product_code, cleaned)
    cleaned = apply_slang_readings(cleaned)        # P0-1: GOAT/aura/fan... → phiên âm Việt (đường Vbee)
    cleaned = _replace_words(cleaned)
    return _MULTISPACE_RE.sub(" ", cleaned).strip(" .,\n\t")


def strip_stage_directions(text: str) -> str:
    return _MULTISPACE_RE.sub(" ", _BRACKETED_RE.sub(" ", text or "")).strip()


def _replace_size(match: re.Match[str]) -> str:
    unit = _UNIT_READINGS.get(match.group(3).lower(), match.group(3))
    return f"{_number(match.group(1))} nhân {_number(match.group(2))} {unit}"


def _replace_number_unit(match: re.Match[str]) -> str:
    unit = _UNIT_READINGS.get(match.group(2).lower(), match.group(2))
    return f"{_number(match.group(1))} {unit}"


def _replace_product_code(match: re.Match[str]) -> str:
    first = _LETTER_READINGS.get(match.group(1).upper(), match.group(1))
    suffix = match.group(3)
    tail = f" {_LETTER_READINGS.get(suffix.upper(), suffix)}" if suffix else ""
    return f"{first} {_number(match.group(2))}{tail}"


def _replace_words(text: str) -> str:
    result = text
    # Tên riêng trước (cụm nhiều từ → từ đơn), rồi tới từ kỹ thuật sản phẩm.
    for source, target in _NAME_READINGS.items():
        result = re.sub(rf"\b{re.escape(source)}\b", target, result, flags=re.I)
    for source, target in _WORD_REPLACEMENTS.items():
        result = re.sub(rf"\b{re.escape(source)}\b", target, result, flags=re.I)
    return result


def _number(value: str) -> str:
    return (value or "").replace(".", ",")
