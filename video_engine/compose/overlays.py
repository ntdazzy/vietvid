r"""Burn text overlay LOCAL bằng drawtext — deterministic, không bao giờ lỗi glyph (V8.3-Q1).

Chữ đọc từ TEXTFILE UTF-8 + ``expansion=none`` → KHÔNG escape nội dung (diệt escape hell);
chỉ còn escape path (Windows ``C:\`` có ``:``). Font vector tiếng Việt đủ dấu.
"""

from __future__ import annotations

import os
import re

# V8.5 (founder): social_proof có SỐ THẬT → hiệu ứng ĐẾM TĂNG (0→N) cho "nổi", KHÔNG bịa số.
_LEADING_INT_RE = re.compile(r"^(\d[\d.,]*)")
_COUNTUP_KINDS = {"social_proof", "proof", "social", "rating"}

_POS_Y = {"top": 0.12, "mid": 0.45, "bottom": 0.68}  # tỉ lệ theo chiều cao khung
_FONT = "assets/fonts/BeVietnamPro-Bold.ttf"
_FALLBACK_FONTS = (
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
)


def _font_path() -> str:
    path = os.path.abspath(_FONT)
    if not os.path.exists(path):
        from core.logger import logger

        path = next((p for p in _FALLBACK_FONTS if os.path.exists(p)), path)
        logger.warning(f"[overlays] thiếu {_FONT} → fallback {path}")
    return _ffpath(path)


def _ffpath(path: str) -> str:
    # ffmpeg filter: '\' -> '/', escape ':' (C\:/...) — tránh crash path Windows.
    return path.replace("\\", "/").replace(":", "\\:")


def _coerce_t(value: object) -> float:
    # Nhận cả schema cũ "2s"/"2" (string) lẫn số giây float.
    try:
        return max(0.0, float(str(value).strip().rstrip("s") or 0))
    except ValueError:
        return 0.0


def _coerce_ypct(value: object) -> float:
    """pos → tỉ lệ y: nhận "top|mid|bottom" HOẶC số 0-1 trực tiếp (CTA tail dùng layout riêng)."""
    pos = str(value or "").strip().lower()
    try:
        return min(0.9, max(0.05, float(pos)))
    except ValueError:
        pass
    for key, ypct in _POS_Y.items():
        if pos.startswith(key):
            return ypct
    return _POS_Y["top"]


def build_drawtext_filters(overlays: list[dict], workdir: str) -> list[str]:
    """overlays: [{"t": 2.0, "text": "399K", "pos": "top", "kind": "price", "dur": 3.0}]
    → list filter drawtext nối vào -vf. Textfile ``ov{i}.txt`` ghi vào ``workdir`` —
    caller (compose) dọn trong ``finally``. Giá (kind=price / có số) = vàng #FFD400 to hơn.
    """
    filters = []
    font = _font_path()
    for i, ov in enumerate(overlays):
        text = str(ov.get("text") or "").strip()[:60]
        if not text:
            continue
        tf = os.path.join(workdir, f"ov{i}.txt")
        with open(tf, "w", encoding="utf-8") as fh:
            fh.write(text)
        t0 = _coerce_t(ov.get("t"))
        dur = max(0.8, _coerce_t(ov.get("dur")) or 3.0)
        ypct = _coerce_ypct(ov.get("pos"))
        is_price = ov.get("kind") == "price" or any(ch.isdigit() for ch in text)
        color = "#FFD400" if is_price else "white"
        # Cap theo CHIỀU RỘNG: drawtext không tự wrap — chữ dài hơn khung sẽ tràn 2 mép.
        # Be Vietnam Pro Bold rộng ~0.62×fontsize/ký tự → fontsize ≤ w*0.92/(0.62*len).
        base = "h/14" if is_price else "h/18"
        size = f"min({base},w*1.48/{max(1, len(text))})"
        # fade-in/out 0.3s (alpha) + slide-up 12px (y) + pill nền đen mờ.
        alpha = (
            f"if(lt(t,{t0}),0,if(lt(t,{t0}+0.3),(t-{t0})/0.3,"
            f"if(lt(t,{t0}+{dur}-0.3),1,({t0}+{dur}-t)/0.3)))"
        )
        # Giá trị bọc '…' trong filtergraph: dấu phẩy bên trong KHÔNG cần escape.
        y = f"h*{ypct}+12*(1-min(max((t-{t0})/0.3,0),1))"
        filters.append(
            f"drawtext=fontfile='{font}':textfile='{_ffpath(os.path.abspath(tf))}':"
            f"expansion=none:fontsize='{size}':fontcolor={color}:"
            f"borderw=2:bordercolor=black@0.55:box=1:boxcolor=black@0.45:boxborderw=18:"
            f"x=(w-text_w)/2:y='{y}':alpha='{alpha}':enable='between(t,{t0},{t0}+{dur})'"
        )
    return filters


def cleanup_overlay_files(workdir: str) -> None:
    """Xoá ov*.txt + overlay.ass trong workdir (gọi từ finally của compose — không tích rác)."""
    try:
        for name in os.listdir(workdir):
            if (name.startswith("ov") and name.endswith(".txt")) or name == "overlay.ass":
                os.remove(os.path.join(workdir, name))
    except OSError:
        pass


# ── Overlay ĐỘNG bằng ASS/libass (V8.4 — hiệu ứng "bóc ra" + "mất đi" premium) ──
_ASS_FONT_NAME = "Be Vietnam Pro"  # family name của BeVietnamPro-Bold.ttf (libass tự dò trong fontsdir)


def _ass_time(seconds: float) -> str:
    """giây → 'H:MM:SS.cc' (ASS dùng centisecond)."""
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _ass_text(text: str) -> str:
    """Escape an toàn cho trường Text của ASS (không cho phá cú pháp tag)."""
    return (
        text.replace("\\", " ").replace("{", "(").replace("}", ")")
        .replace("\r", " ").replace("\n", r"\N")
    )


def _countup_lines(
    raw_text: str, t0: float, dur: float, common: str
) -> list[str] | None:
    """Sinh Dialogue 'ĐẾM TĂNG' cho số dẫn đầu (vd '3400+ ĐÃ BÁN' → 0…3400 trong ~0.6s rồi giữ).

    Số THẬT (không bịa): ramp ease-out kết thúc ĐÚNG giá trị gốc; phần chữ sau số giữ nguyên.
    Trả None nếu không có số dẫn đầu ≥100 (rating nhỏ/không số → dùng anim pop thường).
    """
    m = _LEADING_INT_RE.match(raw_text)
    if not m:
        return None
    digits = re.sub(r"[^\d]", "", m.group(1))
    if not digits or int(digits) < 100:  # số nhỏ / rating "4.8" → không đếm
        return None
    n = int(digits)
    suffix = raw_text[m.end():]  # phần sau số: "+ ĐÃ BÁN | 4.8 SAO"
    ramp = min(0.6, dur * 0.4)
    steps = 12
    out: list[str] = []
    for i in range(steps):
        frac = (i + 1) / steps
        val = int(round(n * (1 - (1 - frac) ** 2)))  # ease-out (nhanh đầu, chậm cuối)
        s, e = t0 + ramp * i / steps, t0 + ramp * (i + 1) / steps + 0.03
        fade = r"\fad(100,0)" if i == 0 else ""
        body = _ass_text(f"{val}{suffix}")
        out.append(
            f"Dialogue: 0,{_ass_time(s)},{_ass_time(e)},Default,,0,0,0,,{{{common}{fade}}}{body}"
        )
    # Bản chính: giữ số THẬT + "mất đi" cuối (KHÔNG pop-in vì đã đếm vào).
    main_ms = int((dur - ramp) * 1000)
    out_ms = max(120, min(280, main_ms - 60))
    main_anim = rf"{{{common}\fad(0,180)\t({max(0, main_ms - out_ms)},{main_ms},\fscx55\fscy55)}}"
    out.append(
        f"Dialogue: 0,{_ass_time(t0 + ramp)},{_ass_time(t0 + dur)},Default,,0,0,0,,"
        f"{main_anim}{_ass_text(raw_text)}"
    )
    return out


def build_ass_overlay_file(
    overlays: list[dict], workdir: str, width: int, height: int
) -> str:
    """Sinh file .ass overlay ĐỘNG → trả path (đã escape cho filter ffmpeg) hoặc "".

    Hiệu ứng mỗi chữ: **bóc ra** (scale 30%→115% overshoot →100% trong ~0.3s + fade-in) →
    giữ → **mất đi** (scale →55% + fade-out ~0.22s cuối). Giá = vàng + to hơn. Outline đen
    đậm + shadow cho đọc rõ trên nền video. Deterministic, GPU encode qua nvenc.
    """
    items = [ov for ov in overlays if str(ov.get("text") or "").strip()]
    if not items:
        return ""
    fs_base = max(18, height // 18)
    style = (
        f"Style: Default,{_ASS_FONT_NAME},{fs_base},&H00FFFFFF,&H000000FF,"
        "&H00101010,&H64000000,-1,0,0,0,100,100,0,0,1,4,2,5,40,40,40,1"
    )
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.601", "",
        "[V4+ Styles]",
        ("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
         "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
         "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding"),
        style, "",
        "[Events]",
        ("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"),
    ]
    cx = width // 2
    for ov in items:
        raw_text = str(ov.get("text") or "").strip()[:60]
        text = _ass_text(raw_text)
        t0 = _coerce_t(ov.get("t"))
        dur = max(1.0, _coerce_t(ov.get("dur")) or 3.0)
        d_ms = int(dur * 1000)
        ypct = _coerce_ypct(ov.get("pos"))
        y = int(height * ypct)
        kind = (ov.get("kind") or "").strip().lower()
        is_price = kind == "price" or any(ch.isdigit() for ch in raw_text)
        is_cta = kind == "cta"
        # màu ASS = &HAABBGGRR; vàng #FFD400 → BBGGRR=00D4FF.
        color = "&H0000D4FF" if is_price else "&H0000C8FF" if is_cta else "&H00FFFFFF"
        fs_kind = int(fs_base * (1.45 if is_price else 1.2 if is_cta else 1.0))
        # CAP theo CHIỀU RỘNG: chữ DÀI font to sẽ TRÀN 2 mép (BeVietnamPro Bold hoa ~0.62×fs/ký
        # tự). fs ≤ width*0.9 / (0.62*len) ≈ width*1.45/len; bù overshoot 110% → dùng 1.3.
        fs_fit = int(width * 1.3 / max(1, len(raw_text)))
        fs = max(20, min(fs_kind, fs_fit))
        common = rf"\an5\pos({cx},{y})\1c{color}\fs{fs}\bord4\shad2"
        # social_proof có SỐ THẬT → ĐẾM TĂNG (0→N) cho "nổi"; còn lại → pop "bóc ra" + "mất đi".
        countup = _countup_lines(raw_text, t0, dur, common) if kind in _COUNTUP_KINDS else None
        if countup:
            lines.extend(countup)
            continue
        out_ms = max(120, min(280, d_ms - 60))
        anim = (
            rf"{{{common}\fad(110,180)\fscx32\fscy32"
            rf"\t(0,160,\fscx110\fscy110)\t(160,300,\fscx100\fscy100)"
            rf"\t({d_ms - out_ms},{d_ms},\fscx55\fscy55)}}"
        )
        lines.append(
            f"Dialogue: 0,{_ass_time(t0)},{_ass_time(t0 + dur)},Default,,0,0,0,,{anim}{text}"
        )
    ass_path = os.path.join(workdir, "overlay.ass")
    with open(ass_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return ass_path


def ass_filter(overlays: list[dict], workdir: str, width: int, height: int) -> list[str]:
    """Trả [filter ass] để nối vào -vf (rỗng nếu không có overlay). Font lấy từ assets/fonts."""
    ass_path = build_ass_overlay_file(overlays, workdir, width, height)
    if not ass_path:
        return []
    fontsdir = os.path.dirname(os.path.abspath(_FONT))
    return [f"ass=f='{_ffpath(os.path.abspath(ass_path))}':fontsdir='{_ffpath(fontsdir)}'"]
