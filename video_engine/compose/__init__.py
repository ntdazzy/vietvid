"""Compose — FFmpeg mux clip Seedance + giọng đọc (nếu có) → final 9:16.

V8.3-Q1: chữ giá/hook/CTA vẽ LOCAL bằng drawtext (``overlays.py`` — textfile UTF-8,
deterministic, không lỗi glyph); Seedance bị CẤM vẽ chữ trong prompt (Director).
V8.3-Q3: đuôi CTA 6s local (``cta_tail.py``) ghép XFADE 0.4s (offset ĐỘNG theo probe) +
loudnorm I=−16 cuối chain — mọi clip cùng loudness social; tắt qua VIDEO_CTA_TAIL_SECONDS=0.
Đánh bóng NHẸ (denoise+sharpen mức thấp) cho video đã đúng resolution — tuyệt đối
KHÔNG AI-upscale nhảy bậc (bịa logo/méo mặt, vi phạm cổng fidelity).
"""

from __future__ import annotations

import os
import shutil
import subprocess

from config.settings import settings
from core.logger import logger
from video_engine.compose.cta_tail import build_cta_tail, probe_video_specs, video_codec_args
from video_engine.compose.overlays import ass_filter, cleanup_overlay_files
from video_engine.providers.base import VideoEngineError


_MUSIC_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

# Chuẩn hoá khung XUẤT cuối về 1080×1920 (9:16 HD) — KHÔNG phải AI-upscale (chỉ lanczos nội suy,
# không bịa chi tiết → không vi phạm cổng fidelity). Vì sao:
#   • Nguồn Seedance 480p = 720×1280; up lanczos→1080 để TikTok coi là HD (cấp bitrate cao hơn,
#     không để player TikTok tự up gây mờ) → clip NÉT hơn rõ rệt khi đăng.
#   • force_original_aspect_ratio=decrease + pad: clip lỡ ra vuông (960×960, do ảnh khung-đầu vuông)
#     sẽ được lồng vào đúng 9:16 (viền đen) thay vì để TikTok cắt méo. setsar=1: pixel vuông.
#   • in_range=pc→out_range=tv giữ nguyên fix dải màu (yuv420p limited) cho Windows.
_FINAL_SCALE_9X16 = (
    "scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos:in_range=pc:out_range=tv,"
    "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
)


# NGÀNH SP → mood track (filename startswith slug). Khớp tên SP/category để nhạc HỢP clip.
_MOOD_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("elegant_luxury", ("nước hoa", "perfume", "serum", "skincare", "kem ", "mỹ phẩm",
                        "làm đẹp", "son", "beauty", "dưỡng", "tinh chất", "nước hồng")),
    ("energetic_edm", ("tai nghe", "sạc", "điện", "laptop", "phone", "tech", "gadget",
                       "máy", "loa", "đồng hồ", "chuột", "bàn phím", "camera")),
    ("upbeat_pop", ("giày", "áo", "quần", "thời trang", "túi", "fashion", "sneaker", "dép", "váy")),
    ("corporate_motivate", ("nồi", "bếp", "gia dụng", "dao", "bình", "đèn", "hút bụi",
                            "nhà", "chảo", "quạt")),
    ("trendy_tiktok", ("bánh", "đồ ăn", "snack", "food", "trà", "cà phê", "kẹo", "ăn vặt")),
    ("chill_lofi", ("bé", "mẹ", "sữa", "baby", "trẻ em", "tã", "khăn sữa", "em bé")),
)


def _pick_bg_music(seed: str = "", hint: str = "", force: bool = False) -> str:
    """Chọn 1 track nhạc nền từ BG_MUSIC_DIR. Ưu tiên HỢP NGÀNH (từ ``hint`` = tên SP+category);
    không khớp → deterministic theo seed (đa dạng). Tắt/không có file → "".

    ``force=True`` (clip KHÔNG LỜI): bỏ qua cờ BG_MUSIC_ENABLED — vì clip không lời BẮT BUỘC có
    nhạc làm tiếng chính (không thì im lặng).
    """
    if not settings.bg_music_enabled and not force:
        return ""
    music_dir = (settings.bg_music_dir or "").strip()
    if not music_dir or not os.path.isdir(music_dir):
        return ""
    tracks = sorted(f for f in os.listdir(music_dir) if f.lower().endswith(_MUSIC_EXTS))
    if not tracks:
        logger.warning(f"[compose] BG_MUSIC_ENABLED nhưng {music_dir} chưa có nhạc — bỏ qua nhạc nền.")
        return ""
    h = (hint or "").lower()
    for slug, kws in _MOOD_KEYWORDS:
        if any(k in h for k in kws):
            match = next((t for t in tracks if t.lower().startswith(slug)), "")
            if match:
                return os.path.join(music_dir, match)
    idx = (sum(ord(c) for c in seed) % len(tracks)) if seed else 0
    return os.path.join(music_dir, tracks[idx])


def _media_dur(path: str) -> float:
    """Độ dài (giây) của file media bất kỳ — 0.0 nếu lỗi."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", path],
            capture_output=True, text=True, timeout=60,
        )
        return float(out.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def compose_final(
    *,
    video_path: str,
    audio_path: str,
    out_path: str,
    narration: str = "",  # giữ tham số cho caller hiện hữu; không còn dùng (phụ đề đã bỏ)
    polish: bool = True,
    keep_source_audio: bool = False,  # native mode: giữ audio Seedance (nhạc+SFX) khi KHÔNG có giọng TTS
    voice_delay_ms: int = 0,  # chừa hook đầu clip (voiceover vào trễ) — KOL im nên không lệch môi
    text_overlays: list[dict] | None = None,  # V8.3-Q1: chữ vẽ local — có overlay là ÉP re-encode
    cta_tail_spec: dict | None = None,  # V8.3-Q3: {product_image, price_text, short_name} → đuôi CTA
    music_path: str = "",  # nhạc nền (rỗng → tự chọn từ BG_MUSIC_DIR nếu BG_MUSIC_ENABLED)
    music_hint: str = "",  # tên SP + category → chọn nhạc HỢP NGÀNH (perfume→elegant, tech→edm...)
) -> str:
    """Mux video + voice + chữ overlay local (+ đuôi CTA xfade). Trả path final.

    Audio (2026-06-13, fix "mấy giọng/khó nghe" — bằng chứng ASR Groq + đối chứng F0):
    - Voiceover (có ``audio_path``): giọng TTS là audio DUY NHẤT. KHÔNG trộn audio Seedance
      vì nó KHÔNG ổn định (lúc nhạc thuần, lúc có vocal/ngân hát) → trộn ở 0.85 cũ làm
      tai nghe ra "giọng thứ 2" + lấn lời. adelay giữ mốc hook khớp overlay; loudnorm
      I=−16 cho loudness chuẩn social.
    - Native (``keep_source_audio=True`` + ``audio_path`` rỗng): giữ nguyên audio Seedance.
    ``text_overlays`` → drawtext nối CÙNG pass polish (1 lần encode); textfile ghi cạnh
    ``out_path`` và dọn trong ``finally``.
    ``cta_tail_spec`` (chỉ chế độ voiceover — có voice): VIDEO_CTA_TAIL_SECONDS>0 →
    build tail từ ảnh SP thật + xfade + loudnorm (1 pass encode chung).
    """
    if shutil.which("ffmpeg") is None:
        raise VideoEngineError("Compose cần ffmpeg trong PATH.")
    if not os.path.exists(video_path):
        raise VideoEngineError(f"Thiếu video để compose: {video_path}")
    workdir = os.path.dirname(out_path) or "."
    os.makedirs(workdir, exist_ok=True)

    tail_s = int(settings.video_cta_tail_seconds or 0)
    has_voice = bool(audio_path) and os.path.exists(audio_path)
    # 2026-06-13: tail chỉ cần CÓ giọng (đã tách khỏi cờ mix cũ — giờ voiceover luôn voice-only).
    use_tail = bool(cta_tail_spec) and tail_s > 0 and has_voice
    # Nhạc nền chỉ cho voiceover (có giọng); tự chọn track nếu BG_MUSIC_ENABLED + có file.
    if has_voice and not music_path:
        music_path = _pick_bg_music(
            seed=os.path.basename(workdir) + (narration or "")[:24], hint=music_hint
        )
    if music_path:
        logger.info(f"[compose] nhạc nền: {os.path.basename(music_path)} (vol={settings.bg_music_volume})")

    muxed = out_path + ".mux.mp4"
    try:
        if use_tail:
            _mux_with_tail(
                video_path,
                audio_path,
                muxed,
                polish=polish,
                voice_delay_ms=voice_delay_ms,
                text_overlays=text_overlays or [],
                workdir=workdir,
                tail_spec=cta_tail_spec or {},
                tail_seconds=tail_s,
                music_path=music_path,
            )
        else:
            _mux(
                video_path,
                audio_path,
                muxed,
                polish=polish,
                keep_source_audio=keep_source_audio,
                voice_delay_ms=voice_delay_ms,
                text_overlays=text_overlays or [],
                workdir=workdir,
                music_path=music_path,
            )
        os.replace(muxed, out_path)
    finally:
        cleanup_overlay_files(workdir)
        # Dọn rác khi compose lỗi: .mux.mp4 (os.replace chưa chạy) + cta_tail.mp4 (tail tạm).
        for tmp in (muxed, os.path.join(workdir, "cta_tail.mp4")):
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
    logger.info(f"[compose] final → {out_path}")
    return out_path


def _mux_with_tail(
    video_path: str,
    audio_path: str,
    out_path: str,
    *,
    polish: bool,
    voice_delay_ms: int,
    text_overlays: list[dict],
    workdir: str,
    tail_spec: dict,
    tail_seconds: int,
    music_path: str | None = None,
) -> None:
    """Clip chính (+overlay) ⟶xfade 0.4s⟶ đuôi CTA; audio = GIỌNG TTS duy nhất xuyên suốt
    (adelay hook + apad qua tail) + loudnorm cuối chain. KHÔNG dùng audio Seedance.
    Có ``music_path`` → nhạc nền SẠCH hạ thấp + sidechain duck dưới giọng (input 3).
    """
    has_music = bool(music_path) and os.path.exists(music_path)
    dur_main, width, height, fps = probe_video_specs(video_path)
    tail_path = os.path.join(workdir, "cta_tail.mp4")
    build_cta_tail(
        product_image=str(tail_spec.get("product_image") or ""),
        price_text=str(tail_spec.get("price_text") or ""),
        short_name=str(tail_spec.get("short_name") or ""),
        seconds=tail_seconds,
        width=width,
        height=height,
        fps=fps,
        out_path=tail_path,
    )
    # 2026-06-13: giọng vượt (main + tail) → giữ khung cuối main cho đủ, tránh -shortest cắt CTA.
    delay = max(0, int(voice_delay_ms))
    voice_end = delay / 1000.0 + _media_dur(audio_path)
    total = dur_main + tail_seconds - 0.4
    extra_main = max(0.0, voice_end - total + 0.2) if voice_end > total + 0.15 else 0.0
    vf_parts: list[str] = []
    if extra_main > 0:
        vf_parts.append(f"tpad=stop_mode=clone:stop_duration={extra_main:.2f}")
    if polish:
        vf_parts.append("hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.4:5:5:0.0")
    if text_overlays:
        vf_parts += ass_filter(text_overlays, workdir, width, height)  # V8.4: chữ động ASS
    main_chain = ",".join(vf_parts) if vf_parts else "null"
    offset = max(0.0, dur_main + extra_main - 0.4)
    vdelay = f",adelay={delay}|{delay}" if delay else ""
    transition = (settings.video_tail_transition or "fade").strip() or "fade"
    # 2026-06-13 (job 36): chuyển full→limited range ngay sau xfade → encoder ghi yuv420p (KHÔNG
    # yuvj420p full-range) → phát phổ thông trên Windows. in_range=pc vì nguồn Seedance/ảnh là full.
    # settb=AVTB CHUẨN HOÁ timebase 2 input TRƯỚC xfade — clip Seedance (1/12288) vs đuôi CTA
    # lavfi/zoompan (1/1000000) lệch timebase thì xfade "do not match" → fail (job 54, tốn $1.2).
    # Mirror product_hero.py:73 (nhánh hero đã có; nhánh tail SỐNG này trước đây bị thiếu).
    vchain = (
        f"[0:v]{main_chain},settb=AVTB[v0];"
        f"[1:v]settb=AVTB[v1];"
        f"[v0][v1]xfade=transition={transition}:duration=0.4:offset={offset:.3f},"
        f"{_FINAL_SCALE_9X16}[v];"
    )
    if has_music:
        # 2026-06-13: nhạc nền âm lượng CỐ ĐỊNH (KHÔNG duck khi có giọng — founder yêu cầu).
        mvol = float(settings.bg_music_volume or 0.20)
        achain = (
            f"[2:a]aresample=48000:async=1{vdelay},apad[vo];"
            f"[3:a]aresample=48000,volume={mvol:.3f}[bg];"
            "[bg][vo]amix=inputs=2:duration=longest:normalize=0,"
            "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        )
    else:
        # Giọng TTS xuyên suốt clip chính + tail (apad im lặng tới hết), loudnorm chuẩn social.
        achain = (
            f"[2:a]aresample=48000:async=1{vdelay},apad,"
            "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        )
    filter_complex = vchain + achain
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", video_path, "-i", tail_path, "-i", audio_path,
    ]
    if has_music:
        cmd += ["-stream_loop", "-1", "-i", music_path]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        *video_codec_args(),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest",
        # +faststart: phát/seek mượt (đồng bộ với _mux) — moov atom lên đầu.
        "-movflags", "+faststart",
        out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise VideoEngineError(f"FFmpeg xfade tail lỗi: {proc.stderr[:300]}")


def _mux(
    video_path: str,
    audio_path: str,
    out_path: str,
    *,
    polish: bool,
    keep_source_audio: bool = False,
    voice_delay_ms: int = 0,
    text_overlays: list[dict] | None = None,
    workdir: str = ".",
    music_path: str | None = None,
) -> None:
    has_voice = bool(audio_path) and os.path.exists(audio_path)
    has_music = bool(music_path) and os.path.exists(music_path)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video_path]
    music_input_idx: int | None = None
    if has_voice:
        cmd += ["-i", audio_path]
    if has_voice and has_music:
        # Nhạc nền (input 2) loop để phủ hết clip; cắt theo -shortest cuối cùng.
        cmd += ["-stream_loop", "-1", "-i", music_path]
        music_input_idx = 2
    elif has_music and not has_voice and not keep_source_audio:
        # Chế độ KHÔNG LỜI: nhạc là tiếng CHÍNH (clip music-only như mẫu TikTok). input 1.
        cmd += ["-stream_loop", "-1", "-i", music_path]
        music_input_idx = 1
    # V8.3-Q1: drawtext nối CÙNG pass với polish (1 lần encode duy nhất);
    # CÓ overlay → ÉP re-encode (cấm -c:v copy — copy thì chữ không vẽ được).
    vf_parts: list[str] = []
    # 2026-06-13: giọng DÀI hơn clip → giữ khung cuối (freeze) cho đủ, tránh -shortest CẮT câu
    # CTA cuối ("liền mạch từ đầu tới cuối"). tpad đặt ĐẦU chain (kéo dài rồi mới polish/overlay).
    if has_voice:
        _vdur = _media_dur(video_path)
        _voice_end = max(0, int(voice_delay_ms)) / 1000.0 + _media_dur(audio_path)
        if _vdur > 0 and _voice_end > _vdur + 0.15:
            vf_parts.append(f"tpad=stop_mode=clone:stop_duration={_voice_end - _vdur + 0.2:.2f}")
    if polish:
        # Đánh bóng nhẹ: khử noise yếu + nét nhẹ — KHÔNG đổi resolution.
        vf_parts.append("hqdn3d=1.5:1.5:6:6,unsharp=5:5:0.4:5:5:0.0")
    if text_overlays:
        # V8.4: chữ overlay ĐỘNG bằng ASS (bóc ra/mất đi) thay drawtext tĩnh.
        _, _ass_w, _ass_h, _ = probe_video_specs(video_path)
        vf_parts += ass_filter(text_overlays, workdir, _ass_w, _ass_h)
    if vf_parts:
        # Chuẩn hoá 1080×1920 (gồm full→limited range) ở cuối chain → nét + đúng 9:16 cho TikTok.
        vf_parts.append(_FINAL_SCALE_9X16)
        cmd += ["-vf", ",".join(vf_parts)]
        cmd += video_codec_args()  # V8.3-Q3.6: libx264 / h264_nvenc theo settings
    else:
        # Trước đây copy giữ nguyên 720p; giờ re-encode 1 lần để chuẩn hoá 1080×1920 (clip thô nét hơn).
        cmd += ["-vf", _FINAL_SCALE_9X16, *video_codec_args()]
    if has_voice:
        # 2026-06-13: GIỌNG TTS là track audio chính (đè 100%, KHÔNG dùng audio Seedance).
        #   - aresample 48k + adelay (chừa hook đầu, khớp mốc overlay) + apad (im lặng tới hết clip).
        #   - loudnorm I=−16 chuẩn loudness social; -shortest chốt độ dài theo video.
        delay = max(0, int(voice_delay_ms))
        vpre = "[1:a]aresample=48000:async=1" + (f",adelay={delay}|{delay}" if delay else "")
        if has_music:
            # 2026-06-13: nhạc nền âm lượng CỐ ĐỊNH (KHÔNG duck khi có giọng — founder yêu cầu).
            # amix normalize=0 giữ nguyên chất 2 track; alimiter chống vỡ; loudnorm chuẩn social.
            mvol = float(settings.bg_music_volume or 0.20)
            achain = (
                f"{vpre},apad[vo];"
                f"[2:a]aresample=48000,volume={mvol:.3f}[bg];"
                "[bg][vo]amix=inputs=2:duration=longest:normalize=0,"
                "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
            )
        else:
            achain = f"{vpre},apad,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        cmd += [
            "-filter_complex", achain,
            "-map", "0:v:0", "-map", "[a]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest",
        ]
    elif keep_source_audio:
        # Native mode: GIỮ audio Seedance sinh sẵn (nhạc + SFX + lip-sync).
        cmd += ["-map", "0:v:0", "-map", "0:a:0?", "-c:a", "aac", "-b:a", "192k", "-ac", "2"]
    elif has_music and music_input_idx is not None:
        # KHÔNG LỜI: nhạc là tiếng chính — volume cao (USER_MUSIC_VOLUME), loudnorm chuẩn social,
        # -shortest cắt nhạc (đã -stream_loop) theo độ dài video.
        mvol = float(settings.user_music_volume or 0.85)
        achain = (
            f"[{music_input_idx}:a]aresample=48000,volume={mvol:.3f},"
            "alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        )
        cmd += [
            "-filter_complex", achain, "-map", "0:v:0", "-map", "[a]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest",
        ]
    else:
        cmd += ["-an"]
    # +faststart: dời moov atom lên đầu → phát/seek mượt khi mở progressive (web + player Windows).
    cmd += ["-movflags", "+faststart", out_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise VideoEngineError(f"FFmpeg mux lỗi: {proc.stderr[:300]}")
