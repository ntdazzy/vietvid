"""Quét CLAIM CẤM trong kịch bản/brief — bảo vệ pháp lý (quảng cáo VN).

Luật VN cấm quảng cáo thổi phồng: thuốc/TPCN "chữa khỏi/100%", mỹ phẩm như thuốc, tài chính
"cam kết lãi/lợi nhuận", tuyệt đối "số 1/tốt nhất". Quét deterministic (không cần key) → trả
cảnh báo theo dòng để UI nhắc người dùng sửa trước khi render. Mặc định CẢNH BÁO (không chặn cứng);
admin có thể siết theo gói sau.
"""

from __future__ import annotations

import re

# (mẫu regex, nhãn, mức) — severity: "block" (rủi ro pháp lý cao) | "warn".
_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bchữa\s+(khỏi|dứt điểm)\b", re.I), "Hứa chữa khỏi bệnh (cấm với TPCN/mỹ phẩm)", "block"),
    (re.compile(r"\b(điều trị|đặc trị)\b", re.I), "Tuyên bố điều trị bệnh", "block"),
    (re.compile(r"\b100\s*%|\bcam kết\s+(khỏi|hiệu quả|kết quả)\b", re.I), "Cam kết tuyệt đối 100%", "warn"),
    (re.compile(r"\bgiảm\s+\d+\s*kg\b|\bgiảm cân\s+(thần tốc|cấp tốc|siêu tốc)\b", re.I), "Hứa giảm cân phi thực tế", "block"),
    (re.compile(r"\b(thay thế thuốc|tốt hơn thuốc)\b", re.I), "So sánh/thay thế thuốc chữa bệnh", "block"),
    (re.compile(r"\bcam kết\s+(lãi|lợi nhuận|sinh lời)\b|\blãi suất\s+cam kết\b", re.I), "Cam kết lợi nhuận tài chính", "block"),
    (re.compile(r"\b(số một|số 1|tốt nhất|nhất việt nam|duy nhất)\b", re.I), "Tuyên bố tuyệt đối 'số 1/tốt nhất' (cần dẫn chứng)", "warn"),
    (re.compile(r"\bkhông tác dụng phụ\b", re.I), "Khẳng định không tác dụng phụ", "warn"),
]


def scan_claims(text: str) -> list[dict]:
    """Trả list {match, label, severity} các claim rủi ro trong text."""
    out: list[dict] = []
    seen: set[str] = set()
    for pat, label, sev in _RULES:
        for m in pat.finditer(text or ""):
            key = f"{label}:{m.group(0).lower()}"
            if key in seen:
                continue
            seen.add(key)
            out.append({"match": m.group(0), "label": label, "severity": sev})
    return out


def scan_script(script: dict) -> list[dict]:
    """Quét toàn bộ lời thoại của 1 kịch bản → gắn beat_index cho dễ định vị trên UI."""
    findings: list[dict] = []
    for i, beat in enumerate(script.get("beats") or []):
        for f in scan_claims(str(beat.get("narration") or "")):
            findings.append({**f, "beat_index": i})
    return findings


def has_blocking(findings: list[dict]) -> bool:
    return any(f.get("severity") == "block" for f in findings)
