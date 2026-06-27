"""asset_resolver.py — biến SPEC chất-liệu {kind, query, entity, hint} của đạo diễn → 1 đường ảnh THẬT.

Bảng định-tuyến mã hoá "luật chất liệu" của kênh (phân tích frame): người thật→Wikimedia; web→og/screenshot;
khái niệm→doodle (Gemini/local); cảm xúc→meme; máy tính/hack→terminal (SINH BẰNG CODE, $0); biến động→
glitch/tv_static (SINH BẰNG CODE). Tái dùng client $0 sẵn (images/*). Anti-repeat qua `used`. FAIL-SOFT:
mọi nhánh lỗi → None; caller (shot_builder) tự lấp (doodle/placeholder/phóng người dẫn) — KHÔNG raise.

KHÔNG biết gì về Shot/Layer/LLM — chỉ "kind + ý đồ → path". Ranh giới rõ cho review.
"""

from __future__ import annotations

import hashlib
import os

from core.logger import logger

W, H = 1920, 1080
_GREEN = (60, 255, 90)

# Bộ meme THẬT iconic dùng "tiết chế" làm punch cà-khịa (nhận ra ngay, biểu cảm rõ, ít chữ Anh). Phần lớn
# meme vẫn là meme-DOODLE nét kênh; chỉ ≤_REAL_MEME_CAP meme thật/video (founder chốt "trộn cả hai").
_ICONIC_MEMES = {
    "drake_hotline_bling.jpg", "surprised_pikachu.jpg", "roll_safe_think_about_it.jpg",
    "mocking_spongebob.jpg", "this_is_fine.jpg", "gru_s_plan.jpg", "evil_kermit.jpg",
    "spiderman_pointing_at_spiderman.jpg", "clown_applying_makeup.jpg", "disaster_girl.jpg",
    "distracted_boyfriend.jpg", "two_buttons.jpg", "laughing_leo.png",
}
_REAL_MEME_CAP = 2


# ── sinh chất liệu BẰNG CODE ($0, không mạng, luôn thành công) ─────────────────
def _mono_font(size: int):
    """Font monospace cho terminal: Consolas (Windows) → font dự án → default."""
    from PIL import ImageFont
    for p in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf",
              os.path.join("storage", "style-research", "fonts", "BeVietnamPro-Black.ttf")):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def _term_subject(hint: str) -> str:
    """Rút 'chủ thể' từ hint cho terminal: cụm IN-HOA/Tên-riêng đầu tiên (ILOVEYOU, Y2K...) → fallback từ dài nhất."""
    import re
    if not hint:
        return "SYSTEM"
    caps = re.findall(r"\b[A-Z][A-Z0-9]{2,}\b", hint)       # ILOVEYOU, Y2K, DDOS...
    if caps:
        return caps[0][:20]
    words = re.findall(r"[A-Za-zÀ-ỹ0-9_]+", hint)
    return (max(words, key=len)[:20] if words else "SYSTEM").upper()


def make_terminal(hint: str, out_dir: str) -> str:
    """Màn terminal đen + chữ xanh + caret nháy — chất 'máy tính/hack/virus' của kênh. BÁM CHỦ ĐỀ: log
    tất định sinh từ chủ thể trong hint (tên virus/lệnh) thay vì 5 dòng cố định. Cache theo hint."""
    from PIL import Image, ImageDraw

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"term_{hashlib.md5((hint or 'x').encode('utf-8')).hexdigest()[:10]}.png")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    subj = _term_subject(hint)
    # số "tất định" theo hash (không random runtime) → đa dạng theo chủ đề mà tái lập được
    seed = int(hashlib.md5((hint or "x").encode("utf-8")).hexdigest()[:6], 16)
    hosts = 1000 + seed % 9_000_000
    pct = 60 + seed % 40
    bar = "#" * (pct // 10) + "." * (10 - pct // 10)
    lines = [
        f"$ ./deploy --target {subj.lower()}",
        f"> loading module {subj} ...",
        f"> [{bar}] {pct}%",
        f"> {subj}: payload injected OK",
        f"> hosts affected: {hosts:,}",
        "> WARNING: system breach detected",
        "$ _",
    ]
    tw, th = 1280, 720
    img = Image.new("RGBA", (tw, th), (8, 10, 12, 255))
    d = ImageDraw.Draw(img)
    font = _mono_font(30)
    y = 60
    for ln in lines:
        d.text((60, y), ln[:52], font=font, fill=_GREEN)
        y += 50
    d.rectangle([110, y - 50, 134, y - 16], fill=_GREEN)   # caret khối dòng cuối
    img.save(out)
    return out


def make_glitch(out_dir: str, *, kind: str = "tv_static") -> str:
    """TV-static / colorbar + nhiễu scanline — chất 'biến động/sốc/lỗi tín hiệu'. Fullbleed 1920×1080. Cache."""
    import numpy as np
    from PIL import Image

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{kind}.png")
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        return out
    # colorbar SMPTE-ish 7 dải dọc + nhiễu hạt + scanline đen dưới đáy (KHÔNG random runtime — pattern cố định)
    bars = [(192, 192, 0), (0, 192, 192), (0, 192, 0), (192, 0, 192), (192, 0, 0), (0, 0, 192), (16, 16, 16)]
    arr = np.zeros((H, W, 3), dtype=np.uint8)
    bw = W // len(bars)
    for i, c in enumerate(bars):
        arr[:, i * bw:(i + 1) * bw] = c
    # nhiễu hạt tất định (dựa chỉ số pixel, không Math.random)
    yy, xx = np.mgrid[0:H, 0:W]
    noise = ((xx * 1103515245 + yy * 12345) % 64).astype(np.uint8)
    arr = np.clip(arr.astype(np.int16) + noise[:, :, None] - 32, 0, 255).astype(np.uint8)
    arr[int(H * 0.82):, :] = (arr[int(H * 0.82):, :] // 3)   # dải scanline tối đáy
    Image.fromarray(arr, "RGB").save(out)
    return out


# ── định tuyến chính ─────────────────────────────────────────────────────────
def _add_used(path: str | None, used) -> str | None:
    if path and used is not None:
        used.add(os.path.basename(path))
    return path


def _flatten_web(path: str | None) -> str | None:
    """5.3 hoà nét ảnh WEB graphics (logo/map/diagram/screenshot) vào palette phẳng kênh: posterize.
    THẬN TRỌNG — chỉ dùng cho graphics, KHÔNG cho real_photo (ảnh người posterize/cartoonify dễ XẤU hơn).
    Tái dùng visual._flatten_doodle (lazy import, fail-soft sẵn)."""
    if not path:
        return path
    try:
        from video_engine.long_narrative.visual import _flatten_doodle
        _flatten_doodle(path)
    except Exception:  # noqa: BLE001
        pass
    return path


def _doodle(beat, hint: str, asset_dir: str, idx: int) -> str | None:
    """Doodle khái niệm: gen ảnh nền trắng theo hint (Gemini/local provider) → tách nền → RGBA. Như _compose_cutout_one."""
    from video_engine.long_narrative import doodle_lib
    from video_engine.long_narrative.images import character_library as clib
    from video_engine.long_narrative.visual import _style_anchor, generate_beat_image

    # Hint nói về CHÍNH NGƯỜI DẪN → KHÔNG vẽ SDXL/Gemini 1 người lạ; trả None để builder dùng PRESENTER THẬT
    # (pose library, nét gốc kênh). Planner yếu (Groq) hay đặt "người dẫn đang nói" thành doodle → chặn ở đây.
    if hint and any(k in hint.lower() for k in ("người dẫn", "nguoi dan", "presenter", "narrator", "mc ")):
        return None
    lib = doodle_lib.lookup(hint)   # Kho nháp đang bị khóa đến khi founder duyệt ảnh final.
    if lib:
        logger.info(f"[asset-resolver] tái dùng doodle_lib cho hint='{hint[:40]}' → {os.path.basename(lib)}")
        return lib
    # cache theo HASH(hint). hint = CHỦ THỂ (resolver ưu tiên query tiếng Anh) → đưa thẳng làm subject_override
    # (DẪN ĐẦU prompt, không nhồi vào extra → SDXL không cắt mất). idx vào hash khi hint rỗng.
    h = hashlib.md5((hint or str(idx)).strip().encode("utf-8")).hexdigest()[:8]
    raw = generate_beat_image(
        beat, os.path.join(asset_dir, f"doodle_{h}.png"), use_character_ref=False,
        style_ref=_style_anchor(), subject_override=hint,
        # BÁM KÊNH GỐC: 1 chủ thể rõ, nét tay mềm, tránh icon cứng/vuông tròn máy móc.
        extra=" ONE SINGLE simple hand-drawn subject, soft playful uneven outline, clear bright flat colors, "
              "large centered with safe white padding, natural non-rigid shape, NO stiff vector icon, "
              "NO square/circle geometric construction, NO background, NO extra characters, plain pure white background.",
    )
    if not raw:
        return None
    return clib.cutout_subject(raw, os.path.join(asset_dir, f"doodle_{h}_cut.png"))


def resolve_content_asset(content: dict, beat, asset_dir: str, *, idx: int = 0,
                          source_urls: list[str] | None = None, used=None) -> str | None:
    """SPEC content {kind, query, entity, hint} → đường ảnh thật (hoặc None nếu hỏng hết → caller lấp).

    idx: số thứ tự shot trong beat (tên file riêng, chống ghi đè). used: set anti-repeat (chia sẻ cả video).
    """
    from video_engine.long_narrative.images import openverse, pixabay
    from video_engine.long_narrative.images.meme_library import match_meme
    from video_engine.long_narrative.images.og_image import og_image_for_article
    from video_engine.long_narrative.images.wikimedia import search_player_photo

    os.makedirs(asset_dir, exist_ok=True)
    source_urls = source_urls or []
    kind = (content.get("kind") or "doodle").strip().lower()
    query = (content.get("query") or "").strip()
    entity = (content.get("entity") or "").strip()
    hint = (content.get("hint") or "").strip()

    try:
        if kind in ("glitch", "tv_static"):
            return make_glitch(asset_dir, kind=kind)
        if kind == "terminal":
            return make_terminal(hint or query, asset_dir)
        if kind == "meme":
            # TRỘN CẢ HAI (founder chốt): phần lớn meme-DOODLE nét kênh; TIẾT CHẾ ≤2 meme THẬT iconic/video
            # làm "punch" cà-khịa (mixed-media). Đếm meme thật đã dùng qua used ∩ ICONIC + giãn theo idx.
            real_done = sum(1 for u in (used or ()) if u in _ICONIC_MEMES)
            if real_done < _REAL_MEME_CAP and idx % 3 == 0:
                m = match_meme(beat, used=used, only=_ICONIC_MEMES)
                if m:
                    return m   # meme THẬT giữ NGUYÊN (KHÔNG posterize — posterize ảnh người → đỏ/vỡ nét, founder báo)
            # mặc định: meme-doodle nét kênh (hài cường điệu). Prompt TIẾNG ANH (SDXL local không hiểu tiếng Việt).
            return _add_used(_doodle(
                beat, "a funny internet meme reaction face, exaggerated comedic expression, "
                      "shocked or laughing hard or crying, big emotion", asset_dir, idx), used)
        if kind == "real_photo":
            p = (search_player_photo(entity, asset_dir) if entity else None)
            if not p and source_urls:
                p = og_image_for_article(source_urls[0], asset_dir)
            p = p or (openverse.search_web_image(query, asset_dir) if query else None)
            p = p or (pixabay.search_web_image(query, asset_dir) if query else None)
            return _add_used(p, used)
        if kind == "logo":
            q = (query or entity) + " logo"
            p = openverse.search_web_image(q, asset_dir) or pixabay.search_web_image(q, asset_dir)
            return _add_used(_flatten_web(p), used)   # 5.3 hoà palette phẳng
        if kind == "screenshot":
            p = (og_image_for_article(source_urls[0], asset_dir) if source_urls else None)
            p = p or openverse.search_web_image((query or entity) + " website screenshot", asset_dir)
            return _add_used(_flatten_web(p), used)   # 5.3 hoà palette phẳng
        if kind in ("map", "diagram"):
            from video_engine.long_narrative import diagram_gen   # 4.3: diagram VS → template PIL nét doodle ($0)
            dg = diagram_gen.make_diagram(hint, kind, asset_dir)
            if dg:
                return _add_used(dg, used)
            q = (query or entity) + (" map" if kind == "map" else " diagram")
            p = _flatten_web(openverse.search_web_image(q, asset_dir) or pixabay.search_web_image(q, asset_dir))
            return _add_used(p or _doodle(beat, hint or query, asset_dir, idx), used)
        if kind == "countryball":
            nat = entity or query
            # ÉP vẽ ĐÚNG quốc kỳ (review: cấm vẽ nhầm cờ nước khác như Algeria→Việt Nam). Bỏ openverse
            # (hay ra ảnh lạc) → doodle với mô tả cờ rõ.
            # NGẮN GỌN (SDXL cắt 77 token) + cờ DẪN ĐẦU để không bị cắt: tên nước + quốc kỳ đúng lên trước.
            p = _doodle(beat, f"{nat} countryball, a round ball painted with the {nat} national flag "
                              f"(correct flag colors), cute simple face, thick black outline", asset_dir, idx)
            return _add_used(p, used)
        # doodle (mặc định): CHỈ gen khi có Ý ĐỒ rõ. ƯU TIÊN query (TIẾNG ANH) cho gen vì SDXL local KHÔNG
        # hiểu tiếng Việt ("cúp vàng vô địch" → ra 2 người ngồi bàn). RỖNG → None = shot NGƯỜI-DẪN THUẦN.
        h2 = query or hint or entity
        return _doodle(beat, h2, asset_dir, idx) if h2 else None
    except Exception as exc:  # noqa: BLE001 — FAIL-SOFT: mọi lỗi nguồn → None, caller lấp
        logger.warning(f"[asset-resolver] kind={kind} lỗi → None: {str(exc)[:120]}")
        return None
