"""render.py — chunk render per-beat → ffmpeg concat -c copy → final (+ Shorts 9:16 + thumbnail).

Mỗi beat = 1 đơn vị render độc lập (chống OOM MoviePy ở video 14' + re-render cục bộ):
  voice (multi-voice) → captions (align) → assets (ảnh/footage) → visual (parallax/nhịp)
  → audio (ducking+foley) → COMPOSE overlay (callout/label/caption/watermark) → beat_N.mp4.
Tất cả beat encode CÙNG thông số (1920×1080 / 24fps / libx264 / aac / 48000) để `concat -c copy`
ghép lossless (Gemini 6.7: hard-cut giữa beat, whoosh nướng đầu/đuôi; KHÔNG crossfade qua concat).
Cache MD5 theo beat (Gemini 6.6): cache_key trùng → giữ beat_N.mp4 cũ, bỏ render lại.
"""

from __future__ import annotations

import json
import os
import subprocess

from config.settings import settings
from core.logger import logger
from video_engine.long_narrative import audio as audio_mod
from video_engine.long_narrative import captions as cap_mod
from video_engine.long_narrative import visual as visual_mod
from video_engine.long_narrative import voice as voice_mod
from video_engine.long_narrative.script_schema import Beat, LongformScript

W, H = 1920, 1080
FPS = 24
_FONT = os.path.join("storage", "style-research", "fonts", "BeVietnamPro-Black.ttf")
LABEL_Y = 52
CALLOUT_Y = 104
CAPTION_Y = 885
CHANNEL_WATERMARK = "ĐIỂM TIN CÀ KHỊA"   # đổi thành tên kênh thật khi chốt branding
_YELLOW = "#ffd23f"
_RENDER_VERSION = "rv28"   # rv28: người dẫn = MẶT-MEME (kho library_meme) nhỏ+sát đáy, nền TRẮNG, BỎ chữ top (founder 2026-06-21)


def _font_path() -> str:
    if os.path.exists(_FONT):
        return _FONT
    # fallback tuyệt đối nếu chạy từ cwd khác
    alt = os.path.join(os.getcwd(), _FONT)
    return alt if os.path.exists(alt) else _FONT


# Chuẩn-hoá CHÍNH TẢ tên riêng trong CHỮ overlay (review: director-LLM gõ "MESSY"). Whitelist NHỎ
# (chỉ ca đã thấy sai); bảo toàn HOA nếu token gốc viết hoa. KHÔNG đụng giọng director (chỉ sửa text hiển thị).
_NAME_FIXES = (("messy", "Messi"),)


def _fix_names(text: str) -> str:
    if not text:
        return text
    import re
    out = text
    for wrong, right in _NAME_FIXES:
        out = re.sub(rf"\b{wrong}\b",
                     lambda m, r=right: r.upper() if m.group(0).isupper() else r,
                     out, flags=re.IGNORECASE)
    return out


def _strip_tail_punct(text: str) -> str:
    """Bỏ dấu câu CUỐI (phẩy/chấm/... ) khi HIỂN THỊ chữ — founder: 'chữ vào clip thì bỏ dấu phẩy cuối'.
    captions.py GIỮ dấu để ngắt cụm (logic nội bộ) → chỉ cắt ở lúc VẼ, KHÔNG đụng captions.py."""
    import re
    return re.sub(r"[\s,\.;:…!?]+$", "", text or "")


def _dedup_words(text: str) -> str:
    """Khử TỪ LẶP LIỀN NHAU trong tiêu đề (vd 'TRUYỀN TRUYỀN THUYẾT' → 'TRUYỀN THUYẾT'). Guard cấu trúc cho
    title/callout do LLM gõ lặp (P0-2). KHÔNG bắt được near-dup khác từ ('Truyện Truyền') — đó là chất lượng LLM."""
    import re
    return re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text or "", flags=re.IGNORECASE | re.UNICODE)


MIN_CAP_SEC = 1.4   # phụ đề hiện TỐI THIỂU 1.4s (cụm 2-3 từ chỉ 0.3-0.9s → đọc không kịp; founder báo)


def _render_beat_clip(beat: Beat, chunks, visual_clip, audio_wav, out_mp4: str) -> None:
    """Compose overlay (callout/label/caption/watermark) lên visual + gắn audio → beat_N.mp4."""
    from moviepy import AudioFileClip, CompositeVideoClip, TextClip, vfx

    font = _font_path()
    d = visual_clip.duration
    # aud/comp khởi tạo None + TOÀN BỘ thân (dựng layer + AudioFileClip + Composite + write) nằm trong try:
    # nếu BẤT KỲ bước nào raise (TextClip lỗi font, AudioFileClip wav hỏng, Composite size mismatch) thì
    # finally vẫn đóng được aud/comp đã tạo + lf_sources (reader b-roll) — đây là NƠI DUY NHẤT đóng chúng.
    aud = None
    comp = None
    try:
        # CHỮ TOP (label 'PHÚT 90' + callout to + watermark tên kênh) ĐÃ BỎ HẲN (founder 2026-06-21):
        # kênh gốc Vui Vẻ KHÔNG có thanh chữ dính top. Chỉ giữ CAPTION nhấn ở đáy (đúng chất kênh gốc).
        layers = [visual_clip]
        # SUB CHỌN LỌC (như Vui Vẻ/Lóng): chỉ hiện cụm NỔI BẬT (hot = chứa từ khoá), KHÔNG sub cả lời —
        # tránh "phụ đề karaoke" lấp màn hình. Callout/label trên đầu vẫn dẫn dắt xuyên suốt.
        # gom cụm HOT trước → biết mốc cụm KẾ để kẹp (không 2 cụm chồng nhau khi kéo dài min-1.4s).
        hots = [(max(0.0, c.start), min(d, c.end), c.text) for c in chunks
                if c.hot and c.text and (min(d, c.end) - max(0.0, c.start)) >= 0.12]
        for i, (s, e, txt) in enumerate(hots):
            nxt = hots[i + 1][0] if i + 1 < len(hots) else d
            disp = max(e - s, MIN_CAP_SEC)                 # P0-3: hiện đủ lâu để đọc kịp
            disp = min(disp, max(0.4, nxt - s), d - s)     # KẸP: không tràn cụm kế / không vượt beat
            layers.append(
                TextClip(font=font, text=_strip_tail_punct(txt).upper(), font_size=52, color=_YELLOW,
                         stroke_color="black", stroke_width=5, method="caption", size=(1480, None),
                         margin=(10, 18))
                .with_position(("center", CAPTION_Y)).with_start(s).with_duration(disp)
                # pop-in: phóng nhẹ 0.82→1.0 + fade ~0.12s đầu → chữ "nảy" vào nhấn mạnh
                .resized(lambda t: 0.82 + 0.18 * min(1.0, t / 0.12))
                .with_effects([vfx.CrossFadeIn(0.10)])
            )
        aud = AudioFileClip(audio_wav)
        comp = CompositeVideoClip(layers, size=(W, H)).with_duration(d).with_audio(aud)
        comp.write_videofile(
            out_mp4, fps=FPS, codec="libx264", audio_codec="aac", audio_fps=48000,
            # temp audio nằm CẠNH beat_NN.mp4 trong work_dir (mặc định MoviePy rớt ở CWD = repo
            # root → kẹt rác *TEMP_MPY*.mp4 khi crash/kill giữa chừng).
            temp_audiofile_path=os.path.dirname(out_mp4) or ".",
            preset="veryfast", threads=(os.cpu_count() or 4), logger=None,
        )
    finally:
        # đóng handle cả ở nhánh lỗi (Windows giữ lock file nếu rò) — chống kẹt temp + lock wav.
        if comp is not None:
            comp.close()
        if aud is not None:
            aud.close()
        # đóng reader VideoFileClip gốc của b-roll (comp.close KHÔNG đóng clip con) — chống rò
        # ffmpeg reader + file handle dồn qua cả video dài (nhiều beat × nhiều shot footage).
        for src in getattr(visual_clip, "lf_sources", None) or []:
            try:
                src.close()
            except Exception:  # noqa: BLE001 — best-effort cleanup, đã đóng/None thì kệ
                pass


def render_beat(beat: Beat, work_dir: str, *, voice_map=None, speed=None,
                visual_mode: str = "doodle", source_urls=None, used=None) -> dict:
    """Render 1 beat → beat_N.mp4 (+ cache MD5). Trả {path, duration, cache_key, voice_blocks}."""
    os.makedirs(work_dir, exist_ok=True)
    bid = beat.beat_id if beat.beat_id is not None else 0
    # visual_mode + tts_engine vào cache_key → đổi mode (doodle↔photo_meme↔hybrid) HOẶC đổi engine
    # giọng (vbee↔gemini) đều bust cache, re-render đúng. Thiếu engine = đổi cờ KHÔNG ăn trên beat cũ.
    tts_engine = (settings.longform_tts_engine or "vbee").strip().lower()
    cache_key = (beat.cache_key(voice_map or voice_mod.VOICE_MAP)
                 + "|" + _RENDER_VERSION + "|" + visual_mode + "|" + tts_engine)
    out_mp4 = os.path.join(work_dir, f"beat_{bid:02d}.mp4")
    meta_path = out_mp4 + ".json"

    # cache: cache_key trùng + file còn → giữ nguyên (incremental render).
    if os.path.exists(out_mp4) and os.path.exists(meta_path):
        try:
            old = json.load(open(meta_path, encoding="utf-8"))
            if old.get("cache_key") == cache_key and os.path.getsize(out_mp4) > 10000:
                logger.info(f"[render] beat {bid} cache HIT → giữ {out_mp4}")
                return old
        except (OSError, json.JSONDecodeError):
            pass

    cache_dir = os.path.join(work_dir, "cache")
    asset_dir = os.path.join(work_dir, "assets")
    # 1) voice
    voice_wav = os.path.join(work_dir, f"voice_{bid:02d}.wav")
    # voice cache DÙNG CHUNG (persistent, KHÔNG bó theo work_dir) → block giọng giống nhau TÁI DÙNG across
    # mọi render → KHÔNG gọi lại Gemini/Vbee TTS trả phí (founder: tái dùng giọng, đừng gọi liên tục).
    bv = voice_mod.synthesize_beat(
        beat, voice_wav, voice_map=voice_map,
        speed=speed or voice_mod.LONGFORM_SPEED, cache_dir=voice_mod.VOICE_CACHE_DIR,
    )
    # 2) captions (align) — truyền bv.blocks (mốc giọng THẬT/block) để caption khớp giọng per-block
    # (trước đây vứt bv.blocks → caption canh cả beat, lệch khi multi-block/ASR fail).
    chunks = cap_mod.align_captions(bv.narration_text, voice_wav, bv.duration, blocks=bv.blocks)
    # 3) assets + visual
    assets = visual_mod.prepare_beat_assets(
        beat, os.path.join(asset_dir, f"b{bid:02d}"),
        visual_mode=visual_mode, source_urls=source_urls, used=used, blocks=bv.blocks,
        duration=bv.duration,
    )
    visual_clip = visual_mod.build_beat_visual(
        beat, bv.duration, image_path=assets["image_path"],
        broll_paths=assets["broll_paths"], bg_path=assets["bg_path"],
        bg_is_scene=assets.get("bg_is_scene", False), blocks=bv.blocks,
        scene_pool=assets.get("scene_pool"), shots=assets.get("shots"),
    )

    # 4) audio mix (ducking + foley + bed)
    bank = audio_mod.ensure_sfx_bank(os.path.join(asset_dir, "sfx"))
    music = audio_mod.pick_music(bv.duration, beat.context, os.path.join(asset_dir, "music"))
    fol = audio_mod.foley_events(bv.narration_text, bv.duration, beat.context, bank, beat_id=bid)
    audio_wav = os.path.join(work_dir, f"audio_{bid:02d}.wav")
    audio_mod.mix_beat_audio(voice_wav, bv.duration, audio_wav, context=beat.context,
                             music_path=music, sfx_events=fol)
    # 5) compose → beat_N.mp4
    _render_beat_clip(beat, chunks, visual_clip, audio_wav, out_mp4)

    meta = {
        "path": out_mp4,
        "duration": bv.duration,
        "cache_key": cache_key,
        "beat_id": bid,
        "speakers": beat.speakers,
        "n_captions": len(chunks),
    }
    json.dump(meta, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False)
    logger.info(f"[render] beat {bid}: {bv.duration:.1f}s, {len(chunks)} caption, "
                f"speakers={beat.speakers} → {out_mp4}")
    return meta


def concat_beats(beat_mp4s: list[str], out_path: str) -> str:
    """Ghép lossless `concat -c copy` (mọi beat cùng thông số). Fallback re-encode nếu copy fail."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    listf = out_path + ".list.txt"
    with open(listf, "w", encoding="utf-8") as f:
        for p in beat_mp4s:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
           "-i", listf, "-c", "copy", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        logger.warning(f"[render] concat -c copy fail → re-encode: {proc.stderr[:200]}")
        cmd2 = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listf,
                "-c:v", "libx264", "-c:a", "aac", "-ar", "48000", "-r", str(FPS), out_path]
        proc2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=900)
        if proc2.returncode != 0:
            raise RuntimeError(f"[render] concat re-encode lỗi: {proc2.stderr[:200]}")
    try:
        os.remove(listf)
    except FileNotFoundError:
        pass
    return out_path


def make_shorts_9x16(src_mp4: str, out_mp4: str, *, max_seconds: float = 55.0) -> str | None:
    """Cắt bản 9:16 (1080×1920) cho TikTok/Shorts: 16:9 lồng GIỮA + nền blur, lấy ~max_seconds đầu.

    Blur-pad (không center-crop) để KHÔNG mất callout/caption ở mép — postable thẳng lên TikTok.
    """
    if not os.path.exists(src_mp4):
        return None
    vf = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=26[bg];"
        "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-t", f"{max_seconds:.1f}", "-i", src_mp4,
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-ar", "48000", out_mp4]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        logger.warning(f"[render] shorts 9:16 lỗi: {proc.stderr[:200]}")
        return None
    return out_mp4


def render_script(
    script: LongformScript,
    work_dir: str,
    out_path: str,
    *,
    beat_indices: list[int] | None = None,
    voice_map=None,
    speed=None,
) -> dict:
    """Render danh sách beat (hoặc toàn bộ) → concat → final. Trả {path, duration, beats[]}."""
    os.makedirs(work_dir, exist_ok=True)
    voice_mod.reset_engine_state()   # bỏ latch credit-out đầu mỗi video → re-thử Gemini khi đã nạp lại
    idxs = beat_indices if beat_indices is not None else list(range(len(script.beats)))
    meta = script.meta or {}
    # P2a: meta (dashboard/script) ưu tiên; KHÔNG có → đọc KEY registry longform_visual_engine (giờ key
    # thực sự có đường-đọc, hết "công tắc chết"); cuối cùng mới 'doodle'.
    visual_mode = meta.get("visual_mode") or (settings.longform_visual_engine or "").strip() or "doodle"
    # 1.2 CHỨNG MINH "công tắc" chảy end-to-end (registry→settings→đây→render_beat): IN visual_mode + nguồn.
    logger.info(f"[render] visual_mode={visual_mode!r} ◀ meta={meta.get('visual_mode')!r} | "
                f"key longform_visual_engine={settings.longform_visual_engine!r} — mode TỚI render_beat")
    source_urls = meta.get("source_urls") or []
    used: set[str] = set()   # chống lặp meme giữa các beat trong 1 video (mode photo_meme/hybrid)
    metas = []
    try:
        for i in idxs:
            beat = script.beats[i]
            metas.append(render_beat(beat, work_dir, voice_map=voice_map, speed=speed,
                                     visual_mode=visual_mode, source_urls=source_urls, used=used))
        final = concat_beats([m["path"] for m in metas], out_path)
        total = sum(m["duration"] for m in metas)
        logger.info(f"[render] FINAL {out_path} | {len(metas)} beat | ~{total:.1f}s")
        return {"path": final, "duration": total, "beats": metas}
    finally:
        # 3.2 nhả VRAM worker local (SDXL giữ 6-9GB) sau khi render xong. No-op với Gemini (mặc định).
        visual_mod.shutdown_image_provider()
