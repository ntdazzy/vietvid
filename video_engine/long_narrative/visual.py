"""visual.py — lớp HÌNH cho long_narrative: ảnh 16:9 + thẻ + parallax 2.5D + nhịp shot + footage.

Trả về VideoClip NỀN (1920×1080) cho 1 beat (đúng `duration`). render.py phủ chữ (callout/label/
caption/watermark) + gắn audio LÊN TRÊN clip này.

Nhịp 3 giây: chia beat thành shot ~4s, xen kẽ THẺ (ảnh AI 16:9 trên nền sân, Ken Burns + parallax)
và FOOTAGE (Pexels b-roll full-bleed) → biến thiên hình, đỡ "slideshow tĩnh". Footage fail-soft:
thiếu key/429/lỗi → tự quay về thẻ ảnh AI (KHÔNG crash pipeline).

API MoviePy 2.x: `with_duration/with_position/with_effects`, `resized(lambda t:)` (Ken Burns),
`vfx.Loop`, `vfx.CrossFadeIn`. KHÔNG dùng API 1.x (`loop/resize/set_*/fx`).
"""

from __future__ import annotations

import hashlib
import os
import re

import httpx
import numpy as np
from PIL import Image, ImageFilter

from config.settings import settings
from core.config_checks import looks_real_secret
from core.logger import logger
from video_engine.long_narrative.script_schema import Beat
from video_engine.long_narrative.visual_shots import (
    CARD_W,
    H,
    SHOT_DUR,
    W,
    _bg_shot,
    _broll_shot,
    _build_layered,
    _card_shot,
    _plan_segments,
    _scene_shot,
    make_card_169,
    stadium_bg,
)


# Style nhất quán cho ảnh AI — khớp nét vẽ kênh "Vui Vẻ" (doodle vẽ tay, ít-AI, hài):
# viền đen DÀY đều + màu PHẲNG đặc (không gradient/shading) + hình tròn trịa đơn giản + mặt tối giản
# (mắt chấm, miệng cong) + biểu cảm "xấu mà vui", kiểu MS-Paint/sổ tay — CỐ TÌNH không bóng bẩy/3D.
STYLE_PREFIX = (
    "Hand-drawn MARKER doodle cartoon, Vietnamese comedy YouTube channel style (Vui Vẻ / Lóng): THICK "
    "slightly WOBBLY uneven hand-drawn black outline (not a perfect vector line), FLAT MUTED colors (soft, "
    "NOT neon-bright), simple rounded shapes, simple expressive face, casual hand-made sketchbook feel, "
    "absolutely NO shading NO gradient. EXAGGERATED funny comedic expression and goofy pose (over-the-top "
    "for laughs, meme-worthy). STRICTLY NOT a clean sticker, NOT generic AI cute, NOT chibi big-head, "
    "NOT 3D, NOT glossy, NOT realistic, NOT dark or horror. Plain white background. No text, no watermark. "
)

# Khuếch-đại HÀI: đa số doodle phải buồn cười/cường-điệu để hút view (founder yêu cầu).
_HUMOR = ("Make it FUNNY and comedic: EXAGGERATED over-the-top facial expression and goofy pose, "
          "absurd cartoon humor, big reaction, meme-worthy, makes the viewer laugh. ")
# KHÔNG ép khung hình ở đây — KHUNG (bán-thân/toàn-thân/toàn-cảnh/cận-cảnh) do ĐẠO DIỄN quyết qua hint
# theo từng cảnh (founder: đừng đè 1 kiểu = đơn điệu). Doodle gen bám hint.
_FRAME_HINT = "Follow the framing described in the subject text (bust / full body / wide scene / close-up). "

# Khi có STYLE-ANCHOR (pose người-dẫn = nét THẬT kênh): ép vẽ THEO NÉT reference, không tả-bằng-chữ.
STYLE_MATCH_PREFIX = (
    "Draw in the EXACT SAME hand-drawn cartoon art style as the reference image: same line quality, same "
    "FLAT but lively coloring, same proportions and simple expressive face, same casual hand-made marker feel. "
    "Use visible simple flat color blocks with slight hand-made texture, not smooth airbrush, not glossy, "
    + _HUMOR + _FRAME_HINT +
    "STRICTLY NOT a bright clean sticker, NOT generic AI cute, NOT chibi big-head, NOT 3D, NOT realistic, "
    "NOT dark. ONE single subject, centered with safe white padding so no hair, hands, fingers, or body parts "
    "are cut off. For face/head requests, use a head-and-shoulders portrait with full hair, ears, chin, and "
    "glasses inside the frame, not an extreme crop. Plain white background, no text. Subject is: "
)
STYLE_MATCH_OBJECT_PREFIX = (
    "Draw the object in the EXACT SAME hand-drawn cartoon art style as the reference image: same wobbly black "
    "outline, same colorful but not neon flat palette and simple marker fills, same simple hand-made marker feel. "
    "Use a few simple uneven color blocks with tiny hand-drawn imperfections, not a smooth icon gradient. ONE single "
    "object only, centered with safe white padding so no part is cut off, plain white paper background, no text. "
    "Keep it as an object, not a character: no arms, no legs, no human body, no extra props, no background scene, "
    "no app icon, no sticker, no stiff vector/icon look, no rigid square/circle construction. Subject is: "
)

_provider = None


def _get_image_provider():
    global _provider
    if _provider is None:
        mode = (settings.longform_image_provider or "local").strip().lower()
        if mode == "local":          # SDXL local ($0, đồng nhất phong cách — Pha B)
            from video_engine.image_stage.local import LocalImageProvider
            _provider = LocalImageProvider()
        else:
            from video_engine.providers.base import ProviderNotConfiguredError

            raise ProviderNotConfiguredError(
                f"LONGFORM_IMAGE_PROVIDER={mode} có thể dùng Gemini image generation. Đặt LONGFORM_IMAGE_PROVIDER=local."
            )
    return _provider


def shutdown_image_provider() -> None:
    """Nhả tài nguyên provider (worker SDXL local giữ 6-9GB VRAM) — GỌI ở finally cuối render. No-op với
    Gemini (không có .shutdown). Reset singleton để video sau spawn worker mới sạch."""
    global _provider
    p = _provider
    _provider = None
    if p is not None and hasattr(p, "shutdown"):
        try:
            p.shutdown()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[image-provider] shutdown lỗi (bỏ qua): {str(exc)[:120]}")


def _character_refs() -> list[str]:
    """Ảnh NHÂN VẬT DẪN cố định (reference) để Gemini giữ nhân vật nhất quán mọi beat.
    Đọc LONGFORM_CHARACTER_REF (1-2 đường dẫn, ngăn phẩy); rỗng/không tồn tại = tắt (hành vi cũ)."""
    raw = (settings.longform_character_ref or "").strip()
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip() and os.path.exists(p.strip())]


def _style_anchor() -> str | None:
    """1 pose người-dẫn SẠCH làm STYLE-ANCHOR → ép Gemini vẽ content ĐÚNG nét tay kênh (không phải
    cute-AI generic). Pose là nét THẬT của kênh. Ưu tiên pose trung tính; fallback pose bất kỳ."""
    d = os.path.join((settings.longform_character_dir or "storage/characters").strip(), "library")
    for name in ("binh_thuong_dung_thang", "noi_chuyen_giai_thich", "tay_ngua_giai_thich"):
        p = os.path.join(d, f"{name}.png")
        if os.path.exists(p):
            return p
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith(".png") and not f.startswith("_"):
                return os.path.join(d, f)
    return None


def _doodle_style_anchor() -> str | None:
    """Ảnh style sạch từ bộ LoRA v11 để đồ vật không bám nhầm style người dẫn/presenter."""
    refs = _doodle_style_refs()
    return refs[0] if refs else None


def _doodle_style_refs() -> list[str]:
    """Vài ảnh train sạch để Gemini nhìn đúng nét Vui Vẻ khi vẽ đồ vật lạ."""
    d = os.path.join("storage", "style-research", "lora", "train_style_v11_clean")
    refs = []
    for name in ("0013_train_final_k040.jpg", "0004_train_final_k006.jpg", "0055_frames_2BEBagp10aQ_0053.jpg"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            refs.append(p)
    if refs:
        return refs
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".jpg", ".png")):
                refs.append(os.path.join(d, f))
                if len(refs) >= 3:
                    break
    return refs


def _flatten_doodle(path: str) -> None:
    """5.1 ÉP PHẲNG ảnh doodle sau gen: posterize (giảm bậc màu) + tăng tương phản → giết gradient/đổ-bóng
    'kiểu AI' mà prompt 'no shading' KHÔNG chặn được (Gemini không tuân đủ). Hoà nét phẳng-viền-đậm của kênh.
    Ghi đè tại chỗ trên ảnh RGB nền-trắng (TRƯỚC cutout). Fail-soft: lỗi → giữ ảnh gốc."""
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
        if not (os.path.exists(path) and os.path.getsize(path) > 5000):
            return
        img = Image.open(path).convert("RGB")
        img = ImageEnhance.Color(img).enhance(1.06)        # giữ màu vừa, tránh icon neon
        img = ImageEnhance.Contrast(img).enhance(1.05)     # viền/khối rõ nhưng không quá sắc
        img = ImageEnhance.Brightness(img).enhance(1.03)   # kéo nhẹ về độ sáng ảnh train
        img = img.filter(ImageFilter.ModeFilter(size=3))   # giảm hạt/mảng bẩn nhỏ, giữ viền đậm
        img = ImageOps.posterize(img, 4)                   # 4 bit/kênh = 16 mức → màu KHỐI PHẲNG, hết gradient
        arr = np.array(img).astype(np.int16)
        edge_px = np.concatenate((arr[:6, :, :].reshape(-1, 3), arr[-6:, :, :].reshape(-1, 3),
                                  arr[:, :6, :].reshape(-1, 3), arr[:, -6:, :].reshape(-1, 3)), axis=0)
        bg = np.median(edge_px, axis=0)
        mask = (np.abs(arr - bg).max(axis=2) < 18) & (arr.mean(axis=2) > 210)
        arr[mask] = 255
        mean = arr.mean(axis=2)
        spread = arr.max(axis=2) - arr.min(axis=2)
        fill = (~mask) & (mean >= 55) & (mean < 155)
        arr[fill] = np.clip(arr[fill] * 1.03 + 6, 0, 255)
        muted_fill = (~mask) & (mean >= 70) & (mean < 190) & (spread < 34)
        arr[muted_fill] = np.clip(arr[muted_fill] * 1.02 + 4, 0, 255)
        vivid_fill = (~mask) & (spread > 90) & (mean > 55)
        arr[vivid_fill] = np.clip(arr[vivid_fill] * 0.82 + 18, 0, 255)
        img = Image.fromarray(arr.astype("uint8"), "RGB")
        img.save(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[flatten] posterize lỗi (giữ gốc): {str(exc)[:100]}")


def generate_beat_image(beat: Beat, out_path: str, *, use_character_ref: bool = True,
                        extra: str = "", style_ref: str | None = None,
                        subject_override: str | None = None) -> str | None:
    """Sinh ảnh cho beat. Cache + fail-soft.

    subject_override: chủ thể RÕ (tiếng Anh) cho B-roll (vd query 'gold trophy') — KHÔNG dùng beat.callout
      (tiếng Việt) làm chủ thể nữa (SDXL không hiểu tiếng Việt + bị nhiễu).
    style_ref: ảnh STYLE-ANCHOR (chỉ dùng đường GEMINI — SDXL local bỏ qua ref).
    `extra`: chèn thêm. LƯU Ý: đổi ref → bump _RENDER_VERSION.
    """
    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
        return out_path
    subject = subject_override or (beat.img_prompt or beat.callout or beat.label)
    style_refs: list[str] = []
    if not use_character_ref:
        subject = " ".join(re.sub(r"\bicons?\b", " ", str(subject), flags=re.IGNORECASE).split())
        style_refs = _doodle_style_refs()
        style_ref = (style_refs[0] if style_refs else None) or style_ref
    refs = _character_refs() if use_character_ref else []
    provider_mode = (settings.longform_image_provider or "local").strip().lower()
    if provider_mode == "local":
        # SDXL cắt prompt ở 77 token → subject (tiếng Anh) DẪN ĐẦU, KHÔNG nhồi STYLE_PREFIX dài
        # (worker tự thêm _STYLE phẳng) → hết "cắt mất chủ thể" + hết nhiễu tiếng Việt.
        prompt = (subject + " " + extra).strip()
        refs = []
    elif style_ref and os.path.exists(style_ref):   # GEMINI: nét theo style-anchor (đúng nét kênh)
        prefix = STYLE_MATCH_PREFIX if use_character_ref else STYLE_MATCH_OBJECT_PREFIX
        prompt = prefix + subject + extra
        refs = (style_refs or [style_ref]) + refs
    else:
        prompt = STYLE_PREFIX + subject + extra
    if refs and use_character_ref:
        prompt += (" Keep the recurring presenter character from the reference image CONSISTENT "
                   "(same face, glasses, hairstyle, outfit) wherever the presenter appears.")
    has_character_ref = bool(refs and use_character_ref)
    try:
        provider = _get_image_provider()
        res = provider.generate(
            prompt=prompt, out_path=out_path, aspect_ratio="16:9", input_image_paths=refs or None
        )
        # CHẶN "ẢNH MA": provider lỗi (local trả None / file rỗng) → KHÔNG trả out_path không tồn tại
        # (caller cutout_subject sẽ vỡ). Kiểm res + file thật.
        if not res and not (os.path.exists(out_path) and os.path.getsize(out_path) > 5000):
            return None
        if not (os.path.exists(out_path) and os.path.getsize(out_path) > 2000):
            return None
        if not has_character_ref:
            _flatten_doodle(out_path)   # 5.1: ép phẳng để hết "vẻ AI" (gradient/bóng)
        try:
            from video_engine.image_stage.local import _generated_image_issues

            issues = _generated_image_issues(out_path, prompt)
            if issues:
                logger.warning(f"[visual] bỏ ảnh sau flatten lỗi {issues}: {out_path}")
                try:
                    os.remove(out_path)
                except OSError:
                    pass
                retry_prompt = (
                    prompt + " Regenerate once more: make the subject larger and fully inside the canvas, "
                    "safe white padding, no edge cut, no duplicate, no tiny subject."
                )
                res = provider.generate(
                    prompt=retry_prompt, out_path=out_path, aspect_ratio="16:9", input_image_paths=refs or None
                )
                if not res or not (os.path.exists(out_path) and os.path.getsize(out_path) > 2000):
                    return None
                if not has_character_ref:
                    _flatten_doodle(out_path)
                issues = _generated_image_issues(out_path, prompt)
                if issues:
                    logger.warning(f"[visual] retry sau flatten vẫn lỗi {issues}: {out_path}")
                    try:
                        os.remove(out_path)
                    except OSError:
                        pass
                    return None
        except Exception:  # noqa: BLE001
            pass
        return out_path
    except Exception as exc:  # noqa: BLE001 — fail-soft: thiếu ảnh → build dùng nền
        logger.warning(f"[visual] ảnh beat {beat.beat_id} lỗi: {str(exc)[:150]}")
        return None


def fetch_pexels_broll(query: str, cache_dir: str) -> str | None:
    """Tải 1 video b-roll Pexels theo query (landscape, ~HD). Cache + fail-soft (Gemini 6.5)."""
    key = (settings.pexels_api_key or "").strip()
    if not looks_real_secret(key, min_length=8):
        return None
    os.makedirs(cache_dir, exist_ok=True)
    out = os.path.join(cache_dir, f"pex_{hashlib.md5(query.encode('utf-8')).hexdigest()}.mp4")
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        return out
    try:
        r = httpx.get(
            "https://api.pexels.com/videos/search",
            params={"query": query, "per_page": 5, "orientation": "landscape", "size": "medium"},
            headers={"Authorization": key},
            timeout=30.0,
        )
        r.raise_for_status()
        for v in r.json().get("videos") or []:
            files = [
                f for f in v.get("video_files", [])
                if f.get("file_type") == "video/mp4" and 1280 <= (f.get("width") or 0) <= 2200
            ]
            files.sort(key=lambda f: f.get("width", 0))
            if not files:
                continue
            dl = httpx.get(files[0]["link"], follow_redirects=True, timeout=120.0)
            dl.raise_for_status()
            with open(out, "wb") as f:
                f.write(dl.content)
            logger.info(f"[visual] Pexels b-roll '{query}' → {out}")
            return out
    except Exception as exc:  # noqa: BLE001 — fail-soft: quay về ảnh AI
        logger.warning(f"[visual] Pexels '{query}' fail-soft: {str(exc)[:150]}")
    return None


def build_beat_visual(
    beat: Beat,
    duration: float,
    *,
    image_path: str | None,
    broll_paths: list[str] | None,
    bg_path: str,
    bg_is_scene: bool = False,
    blocks=None,
    scene_pool: list[str] | None = None,
    shots=None,
) -> "object":
    """Dựng clip NỀN 1920×1080 cho beat (đúng duration): xen kẽ thẻ ảnh + footage, có nhịp + parallax.

    bg_is_scene=True (doodle_cutout): bg_path là ẢNH CẢNH đầy đủ → cắt khung Ken Burns luân phiên
    (động + đa dạng từ 1 ảnh) thay vì drift tĩnh cả beat. False: bg_path là nền sân fallback (drift nhẹ).
    blocks (bv.blocks): cắt shot ĐÚNG ranh lượt nói → hình đổi khớp giọng (đa-giọng nhập vai); khung
    nghiêng về SUBJECT khi nhân vật (speaker != narrator) nói. Rỗng → lưới SHOT_DUR cố định.
    """
    from moviepy import ColorClip, concatenate_videoclips

    # Mode vuive_layered: prepare_beat_assets đã dựng sẵn list[Shot] → render đa-lớp LIVE.
    if shots:
        return _build_layered(shots, duration)

    broll_paths = list(broll_paths or [])
    card_assets = None
    if image_path and os.path.exists(image_path):
        cp, cw, chh = make_card_169(image_path)
        card_assets = (cp, (cw, chh))

    have_card = card_assets is not None
    have_broll = bool(broll_paths)
    shots = []
    sources = []  # reader VideoFileClip gốc của b-roll → render đóng sau khi xuất (chống rò handle/RAM)
    segments = _plan_segments(duration, blocks)
    # Bao thân trong try: nếu _card_shot/_bg_shot HOẶC concatenate_videoclips raise SAU khi đã mở reader
    # b-roll (vào `sources`), out.lf_sources=... không bao giờ chạy → reader mồ côi (render không nhận
    # được clip để đóng). except đóng sạch sources rồi re-raise (giữ nguyên control flow fail-soft trên).
    try:
        for idx, (_seg_start, sd, bi) in enumerate(segments):
            shot = None
            # Ưu tiên xen kẽ thẻ↔footage. THIẾU thẻ (ảnh AI 504) → footage MỌI shot; THIẾU footage → thẻ;
            # thiếu CẢ hai → nền sân Ken Burns (KHÔNG để màn đen phẳng — fix blank-frame).
            want_broll = have_broll and ((not have_card) or idx % 2 == 1)
            if want_broll:
                try:
                    shot = _broll_shot(broll_paths[idx % len(broll_paths)], sd)
                except Exception as exc:  # noqa: BLE001 — fail-soft: footage lỗi → thẻ/nền
                    logger.warning(f"[visual] broll shot lỗi → fallback: {str(exc)[:120]}")
                    shot = None
            if shot is None and have_card:
                shot = _card_shot(card_assets[0], card_assets[1], bg_path, sd, zoom_in=(idx % 2 == 0))
            if shot is None:
                # doodle_cutout: mỗi shot dùng CẢNH CỦA BLOCK đó (scene_pool[bi]) → hình đổi theo lượt nói;
                # Ken Burns nhẹ giữ bố cục. Không có scene_pool → 1 cảnh bg_path. Khác mode → nền sân drift.
                if bg_is_scene:
                    scene = scene_pool[min(bi, len(scene_pool) - 1)] if scene_pool else bg_path
                    shot = _scene_shot(scene, sd, idx)
                else:
                    shot = _bg_shot(bg_path, sd)
            src = getattr(shot, "lf_source", None)
            if src is not None:
                sources.append(src)
            shots.append(shot)

        if not shots:
            out = ColorClip(size=(W, H), color=(12, 18, 30)).with_duration(duration)
        elif len(shots) == 1:
            out = shots[0].with_duration(duration)
        else:
            out = concatenate_videoclips(shots, method="compose").with_duration(duration)
    except BaseException:
        for s in sources:
            try:
                s.close()
            except Exception:  # noqa: BLE001 — best-effort: đã đóng/None thì kệ
                pass
        raise
    out.lf_sources = sources
    return out


def _resolve_photo_meme_asset(beat: Beat, asset_dir: str, source_urls: list[str], used) -> str | None:
    """Mode photo_meme/hybrid: trả 1 ẢNH THẬT (cầu thủ Wikimedia / og:image bài tin) HOẶC MEME khớp cảm
    xúc beat. Xen kẽ giống reel (beat chẵn+có photo_subject → nghiêng ảnh thật; lẻ/joke/drama/climax →
    nghiêng meme). KHÔNG gọi Gemini → né 504. Fail-soft → None (build_beat_visual dùng nền sân động)."""
    from video_engine.long_narrative.images.meme_library import match_meme
    from video_engine.long_narrative.images.og_image import og_image_for_article
    from video_engine.long_narrative.images.wikimedia import search_player_photo

    bid = beat.beat_id or 0
    lean_meme = (bid % 2 == 1) or (beat.context in {"joke", "drama", "climax"})

    def _photo() -> str | None:
        p = search_player_photo(beat.photo_subject, asset_dir) if beat.photo_subject else None
        if not p and source_urls:
            p = og_image_for_article(source_urls[0], asset_dir)
        if not p:
            # mở rộng nguồn ảnh $0 (commercial-OK): Openverse (CC/PD, no key) → Pixabay (key) — theo
            # entity rồi keyword footage. Nâng tỉ lệ ra-được-ảnh-thật cho beat không có ở Wikimedia.
            from video_engine.long_narrative.images import openverse, pixabay
            for q in (beat.photo_subject, *(beat.broll_keywords or [])[:2]):
                q = (q or "").strip()
                if not q:
                    continue
                p = openverse.search_web_image(q, asset_dir) or pixabay.search_web_image(q, asset_dir)
                if p:
                    break
        return p

    def _meme() -> str | None:
        return match_meme(beat, used=used)

    first, second = (_meme, _photo) if lean_meme else (_photo, _meme)
    return first() or second() or None


def _is_presenter_subject(beat: Beat) -> bool:
    import re

    text = " ".join(
        str(getattr(beat, key, "") or "") for key in ("img_prompt", "callout", "label")
    ).lower()
    if any(term in text for term in ("người dẫn", "nguoi dan")):
        return True
    return any(re.search(rf"\b{term}\b", text) for term in ("presenter", "narrator", "host", "mc"))


def _cutout_subject_prompt(beat: Beat, hint: str = "") -> str:
    import re

    def _has_key(src: str, key: str) -> bool:
        return re.search(rf"\b{re.escape(key)}\b", src) is not None

    visual_text = " ".join(
        str(part or "") for part in (hint, beat.img_prompt, beat.callout, beat.label)
    ).lower()
    text = " ".join(
        str(part or "") for part in (visual_text, beat.narration_text, " ".join(beat.broll_keywords or []))
    ).lower()
    if any(term in visual_text for term in ("mountain", "summit", "peak", "journey", "hành trình", "hanh trinh")):
        return "mountain peak"
    if any(term in visual_text for term in ("record", "records", "kỷ lục", "ky luc", "di sản", "di san", "legacy", "library", "book")):
        return "open book"
    if any(term in visual_text for term in ("save", "cản phá", "can pha", "cứu thua", "cuu thua", "deflect")):
        return "goalkeeper glove"
    if any(term in visual_text for term in ("penalty", "referee", "play on", "đòi 11m", "doi 11m", "đòi penalty", "doi penalty")):
        return "small whistle"
    if any(term in visual_text for term in ("trophy", "cup", "world cup", "cúp", "cup", "champion")):
        return "simple trophy"
    if any(term in visual_text for term in ("tv", "watching", "couch")):
        return "tv screen"
    if any(term in visual_text for term in ("footballer", "football player", "soccer player", "soccer balls", "soccer ball")):
        return "simple soccer player full body"
    if any(term in visual_text for term in ("tuổi", "tuoi", "birthday", "cake", "38", "candles")):
        return "birthday cake"
    scoring_terms = (
        "goal", "bàn thắng", "ban thang", "ghi bàn", "ghi ban", "hat-trick", "hattrick",
        "cú sút", "cu sut", "sút", "sut", "bottom corner", "vào lưới", "vao luoi",
        "tỉ số", "ti so", "scoreboard", "3-0", "2-0", "rebound", "đệm bồi", "dem boi",
    )
    if any(term in text for term in scoring_terms):
        if any(term in text for term in ("net", "lưới", "luoi", "khung thành", "khung thanh")):
            return "goal net"
        return "soccer ball"
    if any(term in text for term in ("save", "cản phá", "can pha", "goalkeeper save", "thủ môn", "thu mon", "cứu thua", "cuu thua")):
        return "goalkeeper glove"
    choices = (
        ("small subscribe bell", ("subscribe", "bell", "like button")),
        ("small whistle", ("referee", "penalty", "offside")),
        ("red card", ("red card", "thẻ đỏ", "the do")),
        ("yellow card", ("yellow card", "thẻ vàng", "the vang")),
        ("goal net", ("goal net", "goal post", "khung thành", "khung thanh")),
        ("goalkeeper glove", ("goalkeeper", "save")),
        ("simple trophy", ("world cup", "trophy", "cup", "champion crown")),
        ("simple crown", ("crown", "king", "throne")),
        ("open book", ("book", "library", "record", "records", "legend", "legends", "history", "number")),
        ("bar chart", ("bar chart", "chart", "ranking", "rank", "biểu đồ", "bieu do")),
        ("clock", ("clock", "time", "đồng hồ", "dong ho")),
        ("question mark", ("question", "why", "?", "câu hỏi", "cau hoi")),
        ("warning sign", ("warning", "caution", "alert", "cảnh báo", "canh bao")),
        ("mountain peak", ("mountain", "summit", "peak", "timeline", "road", "journey", "years")),
        ("birthday cake", ("birthday cake", "cake", "candles")),
        ("tv screen", ("tv", "screen")),
        ("simple soccer player full body", ("footballer", "soccer player", "football player", "cầu thủ", "cau thu")),
        ("soccer ball", ("soccer ball", "football", "stadium", "pitch", "fans", "ball")),
    )
    for subject, keys in choices:
        if any(_has_key(text, k) for k in keys):
            return subject
    fallback_src = next(
        (str(part or "").strip().lower() for part in (beat.img_prompt, beat.callout, beat.label, hint)
         if str(part or "").strip()),
        text,
    )
    words = [w.strip(" ,.;:!?()[]{}\"'") for w in fallback_src.split()]
    banned = {
        "a", "an", "the", "of", "and", "with", "in", "on", "at", "to", "from", "for", "no", "text",
        "caricature", "dramatic", "cinematic", "humorous", "emotional", "style", "scene",
    }
    short = " ".join(w for w in words if w and w not in banned)[:70].strip()
    if short:
        logger.info(f"[visual] cutout subject fallback to prompt doodle: {short[:70]}")
        return short
    logger.info("[visual] cutout subject fallback to football doodle")
    return "simple football"


def _cutout_good_enough(path: str | None) -> bool:
    if not path or not os.path.exists(path):
        return False
    try:
        import numpy as np

        im = Image.open(path).convert("RGBA")
        a = np.array(im)[:, :, 3]
        ys, xs = np.where(a > 10)
        if not len(xs):
            return False
        w, h = im.size
        bw, bh = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
        if bw < 80 or bh < 80:
            return False
        if bw / max(1, bh) > 3.2 or bh / max(1, bw) > 3.2:
            return False
        edge = max(3, min(w, h) // 35)
        edge_px = (
            int((a[:edge, :] > 10).sum()) + int((a[-edge:, :] > 10).sum()) +
            int((a[:, :edge] > 10).sum()) + int((a[:, -edge:] > 10).sum())
        )
        return edge_px / max(1, int((a > 10).sum())) < 0.10
    except Exception:
        return False


def _static_icon_subject(subject: str, out_path: str) -> str | None:
    name = (subject or "").lower()
    try:
        from PIL import ImageDraw

        size = 768
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        black = (18, 18, 18, 255)
        gray = (238, 238, 232, 255)
        yellow = (242, 204, 86, 255)
        blue = (80, 190, 214, 255)
        green = (105, 190, 98, 255)
        pink = (232, 104, 178, 255)
        red = (218, 70, 56, 255)
        lw = 24

        if "crown" in name:
            pts = [(150, 500), (210, 270), (325, 430), (384, 235), (443, 430), (558, 270), (618, 500)]
            d.polygon(pts, fill=yellow, outline=black)
            d.line(pts + [pts[0]], fill=black, width=lw, joint="curve")
            d.rounded_rectangle((175, 500, 593, 585), radius=28, fill=yellow, outline=black, width=lw)
            for x, y in ((210, 270), (384, 235), (558, 270)):
                d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=gray, outline=black, width=12)
        elif "whistle" in name:
            d.ellipse((185, 270, 505, 560), fill=yellow, outline=black, width=lw)
            d.ellipse((270, 360, 380, 470), fill=gray, outline=black, width=18)
            d.rounded_rectangle((470, 345, 635, 455), radius=30, fill=blue, outline=black, width=lw)
            d.arc((155, 235, 575, 600), 200, 330, fill=black, width=16)
        elif "glove" in name:
            d.rounded_rectangle((205, 260, 555, 570), radius=80, fill=blue, outline=black, width=lw)
            for x in (255, 325, 395, 465):
                d.rounded_rectangle((x, 155, x + 78, 390), radius=38, fill=blue, outline=black, width=lw)
            d.line((235, 465, 545, 465), fill=yellow, width=16)
            d.line((245, 520, 515, 520), fill=yellow, width=12)
        elif "bell" in name or "subscribe" in name:
            d.pieslice((235, 205, 533, 585), 180, 360, fill=yellow, outline=black, width=lw)
            d.rounded_rectangle((215, 415, 553, 575), radius=38, fill=yellow, outline=black, width=lw)
            d.ellipse((340, 560, 428, 648), fill=yellow, outline=black, width=lw)
            d.arc((275, 115, 493, 260), 200, 340, fill=black, width=18)
        elif "trophy" in name or "cup" in name:
            d.rounded_rectangle((280, 190, 488, 470), radius=35, fill=yellow, outline=black, width=lw)
            d.arc((170, 220, 310, 410), 85, 280, fill=black, width=lw)
            d.arc((458, 220, 598, 410), 260, 95, fill=black, width=lw)
            d.line((384, 470, 384, 575), fill=black, width=lw)
            d.rounded_rectangle((275, 575, 493, 635), radius=25, fill=yellow, outline=black, width=lw)
        elif "book" in name:
            d.polygon([(160, 235), (375, 295), (375, 590), (160, 530)], fill=(252, 242, 199, 255), outline=black)
            d.polygon([(608, 235), (393, 295), (393, 590), (608, 530)], fill=(252, 242, 199, 255), outline=black)
            d.line((384, 300, 384, 600), fill=black, width=lw)
            for y in (345, 405, 465):
                d.line((200, y, 335, y + 35), fill=green, width=10)
                d.line((568, y, 433, y + 35), fill=green, width=10)
        elif "mountain" in name:
            d.polygon([(95, 610), (335, 210), (535, 610)], fill=(244, 124, 178, 255), outline=black)
            d.polygon([(335, 210), (435, 377), (376, 350)], fill=(255, 255, 255, 255), outline=black)
            d.polygon([(330, 610), (535, 285), (690, 610)], fill=(80, 190, 214, 255), outline=black)
            d.polygon([(535, 285), (610, 430), (565, 402)], fill=(255, 255, 255, 255), outline=black)
            d.line((95, 610, 690, 610), fill=black, width=lw)
            d.arc((190, 510, 520, 700), 190, 340, fill=green, width=18)
        elif "cake" in name:
            d.rounded_rectangle((180, 360, 588, 595), radius=36, fill=(244, 172, 180, 255), outline=black, width=lw)
            d.rectangle((220, 275, 250, 360), fill=yellow, outline=black)
            d.rectangle((370, 255, 400, 360), fill=yellow, outline=black)
            d.rectangle((520, 275, 550, 360), fill=yellow, outline=black)
            for x in (235, 385, 535):
                d.polygon([(x, 235), (x - 22, 270), (x + 22, 270)], fill=red, outline=black)
        elif "tv" in name:
            d.rounded_rectangle((140, 215, 628, 555), radius=45, fill=red, outline=black, width=lw)
            d.rounded_rectangle((185, 255, 520, 500), radius=22, fill=(156, 231, 246, 255), outline=black, width=16)
            d.polygon([(205, 480), (315, 335), (405, 455), (470, 360), (520, 500), (185, 500)],
                      fill=green, outline=black)
            d.polygon([(205, 480), (315, 335), (405, 455), (470, 360), (520, 500), (185, 500)],
                      outline=black)
            d.ellipse((535, 275, 580, 320), fill=yellow, outline=black, width=10)
            d.ellipse((540, 355, 575, 390), fill=blue, outline=black, width=10)
            d.line((320, 545, 255, 625), fill=black, width=lw)
            d.line((448, 545, 513, 625), fill=black, width=lw)
            d.line((270, 625, 498, 625), fill=black, width=lw)
        elif "ball" in name or "football" in name or "soccer" in name:
            d.ellipse((165, 165, 603, 603), fill=gray, outline=black, width=lw)
            d.polygon([(384, 285), (455, 340), (430, 430), (338, 430), (313, 340)], fill=pink, outline=black)
            for p, c in (((245, 245), blue), ((530, 260), yellow), ((230, 520), pink), ((535, 500), green)):
                d.ellipse((p[0] - 35, p[1] - 35, p[0] + 35, p[1] + 35), fill=c, outline=black, width=10)
            d.line((313, 340, 245, 245), fill=black, width=12)
            d.line((455, 340, 530, 260), fill=black, width=12)
            d.line((338, 430, 230, 520), fill=black, width=12)
            d.line((430, 430, 535, 500), fill=black, width=12)
        else:
            return None

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        img.save(out_path)
        return out_path
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[visual] static icon lỗi: {str(exc)[:100]}")
        return None


def _compose_cutout_one(beat: Beat, asset_dir: str, source_urls: list[str], used, *,
                        idx: int = 0, hint: str = "") -> str | None:
    """1 CẢNH doodle_cutout (cho 1 block): pose nhân vật cut-out + ảnh SUBJECT doodle theo `hint` (lời
    block → ảnh khớp KHOẢNH KHẮC đó) → 1 ảnh full-scene. idx → tên file riêng + đổi bên người dẫn.
    Fail-soft → None."""
    from video_engine.long_narrative.images import character_library as clib
    from video_engine.long_narrative.images.cutout_compose import compose_beat_scene

    name = clib.pick_pose(beat, used=used)   # used chia sẻ → mỗi block 1 pose khác (anti-repeat)
    if not name:
        return None
    char = clib.pose_asset(name)
    if not char:
        return None
    # subject doodle theo KHOẢNH KHẮC block (hint) → mỗi block 1 hình khác; gen NỀN TRẮNG rồi tách nền.
    subject = None
    if not _is_presenter_subject(beat):
        moment = f" Cảnh minh hoạ khoảnh khắc: {hint[:120]}." if hint else ""
        base_subject = _cutout_subject_prompt(beat, hint)
        try:
            from video_engine.long_narrative.doodle_lib import lookup as lookup_doodle

            subject = lookup_doodle(base_subject)
        except Exception:
            subject = None
        if not subject:
            for attempt in range(3):
                suffix = "" if attempt == 0 else f" variant {attempt}"
                subj_raw = generate_beat_image(
                    beat, os.path.join(asset_dir, f"subj_b{beat.beat_id}_{idx}_{attempt}.png"), use_character_ref=False,
                    subject_override=base_subject + suffix,
                    extra=moment + " A SINGLE isolated subject on a PLAIN PURE WHITE background, no scenery, centered.",
                )
                cut = clib.cutout_subject(
                    subj_raw, os.path.join(asset_dir, f"subj_b{beat.beat_id}_{idx}_{attempt}_cut.png")
                ) if subj_raw else None
                if _cutout_good_enough(cut):
                    subject = cut
                    break
        if not subject:
            subject = _resolve_photo_meme_asset(beat, asset_dir, source_urls, used)
        if not subject:
            logger.warning(
                f"[visual] bỏ cảnh doodle_cutout beat {beat.beat_id}/{idx}: thiếu ảnh chính đạt chuẩn ({base_subject[:100]})"
            )
            return None
    out = os.path.join(asset_dir, f"scene_b{beat.beat_id}_{idx}.png")
    side = "left" if idx % 2 == 0 else "right"
    try:
        return compose_beat_scene(char, subject, out, char_side=side)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[visual] compose cutout beat {beat.beat_id}/{idx} lỗi: {str(exc)[:120]}")
        return None


def prepare_beat_assets(beat: Beat, asset_dir: str, *, visual_mode: str = "doodle",
                        source_urls: list[str] | None = None, used=None, blocks=None,
                        duration: float = 0.0) -> dict:
    """Sinh sẵn ảnh + tải footage cho 1 beat → dict {image_path, broll_paths, bg_path[, scene_pool]}.

    visual_mode: doodle (Gemini, mặc định) · photo_meme (ảnh thật+meme, KHÔNG Gemini → né 504) ·
    hybrid (beat chẵn doodle, beat lẻ ảnh thật/meme; fallback chéo) · doodle_cutout (look Vui Vẻ).
    blocks (bv.blocks): doodle_cutout sinh 1 CẢNH RIÊNG cho MỖI block (hình đổi theo lượt nói → nhiều
    asset/video, đổi hình mỗi 3-4s). Tách khỏi build_beat_visual để cache I/O.
    """
    os.makedirs(asset_dir, exist_ok=True)
    source_urls = source_urls or []
    # vuive_layered: đạo diễn AI sinh list[Shot] đa-lớp (shot tự có lớp bg kem → KHÔNG cần stadium_bg).
    # Hỏng (planner [] / build rỗng) → rơi xuống doodle_cutout (look đã chứng minh) = "không tệ hơn bây giờ".
    if visual_mode == "vuive_layered":
        from video_engine.long_narrative import shot_builder, shot_planner
        specs = shot_planner.plan_beat_shots(beat, blocks, duration) if duration > 0 else []
        if specs:
            segments = _plan_segments(duration, blocks)
            shots = shot_builder.build_shots_for_beat(
                specs, segments, beat, asset_dir, source_urls=source_urls, used=used)
            if shots:
                return {"image_path": None, "broll_paths": [], "bg_path": "", "shots": shots}
        logger.info(f"[visual] vuive_layered beat {beat.beat_id}: planner rỗng → fallback doodle_cutout")
        visual_mode = "doodle_cutout"
    bg_path = stadium_bg(os.path.join(asset_dir, "bg_stadium.png"))   # chỉ tính khi THỰC SỰ cần nền sân
    if visual_mode == "photo_meme":
        image_path = _resolve_photo_meme_asset(beat, asset_dir, source_urls, used)
    elif visual_mode == "hybrid":
        def _gen():
            return generate_beat_image(beat, os.path.join(asset_dir, f"img_b{beat.beat_id}.png"))
        def _pm():
            return _resolve_photo_meme_asset(beat, asset_dir, source_urls, used)
        first, second = (_gen, _pm) if (beat.beat_id or 0) % 2 == 0 else (_pm, _gen)
        image_path = first() or second()
    elif visual_mode == "doodle_cutout":
        # Look Vui Vẻ: MỖI block 1 cảnh riêng (subject doodle theo lời block) → đổi hình theo lượt nói,
        # nhiều asset/video, giữ nét thuần doodle. Trả scene_pool[]; build_beat_visual map shot↔block.
        blks = list(blocks or [])
        pool: list[str] = []
        for i, blk in enumerate(blks):
            sc = _compose_cutout_one(beat, asset_dir, source_urls, used, idx=i,
                                     hint=getattr(blk, "text", "") or "")
            if sc:
                pool.append(sc)
        if not pool:  # không có blocks / gen lỗi hết → 1 cảnh như cũ
            sc = _compose_cutout_one(beat, asset_dir, source_urls, used, idx=0, hint="")
            if sc:
                pool = [sc]
        if pool:
            return {"image_path": None, "broll_paths": [], "bg_path": pool[0],
                    "bg_is_scene": True, "scene_pool": pool}
        image_path = generate_beat_image(beat, os.path.join(asset_dir, f"img_b{beat.beat_id}.png"))
    else:  # doodle (mặc định) — giữ NGUYÊN hành vi cũ
        image_path = generate_beat_image(beat, os.path.join(asset_dir, f"img_b{beat.beat_id}.png"))
    broll_paths: list[str] = []
    # Footage Pexels MẶC ĐỊNH TẮT (longform_broll_enabled): stock theo keyword hay LẠC ĐỀ + lệch phong
    # cách "tranh vẽ AI" của kênh. Khi tắt → hình = ảnh vẽ AI (Gemini) + nền sân fallback, KHÔNG footage thật.
    if settings.longform_broll_enabled and beat.image_source in {"stock", "ai", "news"}:
        for kw in (beat.broll_keywords or [])[:2]:
            p = fetch_pexels_broll(kw, os.path.join(asset_dir, "broll"))
            if p:
                broll_paths.append(p)
    return {"image_path": image_path, "broll_paths": broll_paths, "bg_path": bg_path}
