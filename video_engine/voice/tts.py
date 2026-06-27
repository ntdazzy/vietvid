"""TTSEngine — chuyển kịch bản thành giọng đọc tiếng Việt (vbee → edge-tts).

V8.2 D2/D3: Kokoro + ElevenLabs đã xoá — fallback còn vbee (trả phí) → edge-tts (free).
Mỗi lần render thêm dao động nhẹ pitch/rate (±~1.5%) cho giọng tự nhiên giữa các bản.
Chế độ giả lập (USE_FAKE_CLIENTS): nếu edge-tts lỗi (vd không có mạng) sẽ sinh audio
câm theo độ dài ước lượng để vẫn demo được toàn trình offline.
"""

from __future__ import annotations

import os
import random
import subprocess

import edge_tts

from config.settings import settings
from core.exceptions import RenderError
from core.logger import logger
from core.mixins import GPUResourceMixin
from video_engine.compose.ffmpeg import FFmpegProcessor


class TTSEngine(GPUResourceMixin):
    def __init__(self) -> None:
        self.voice = settings.tts_voice
        self.jitter = settings.tts_jitter_pct
        self.speed = float(settings.voice_speed or 1.0)  # nói nhanh hơn (rate base cho edge)

    async def _synthesize_one(self, text: str, out_path: str) -> float:
        # edge-tts yêu cầu rate là % NGUYÊN và pitch là Hz nguyên (không nhận thập phân).
        bound = max(1, int(round(self.jitter)))
        base = int(round((self.speed - 1.0) * 100))  # voice_speed → rate base (nói nhanh hơn)
        rate_s = f"{base + random.randint(-bound, bound):+d}%"
        pitch_s = f"{random.randint(-3, 3):+d}Hz"
        try:
            comm = edge_tts.Communicate(text, self.voice, rate=rate_s, pitch=pitch_s)
            await comm.save(out_path)
        except Exception as exc:  # noqa: BLE001
            if settings.use_fake_clients:
                logger.warning(f"TTS lỗi ({exc}); chế độ giả lập → sinh audio câm.")
                self._silent_fallback(text, out_path)
            else:
                raise RenderError(f"edge-tts lỗi: {exc}") from exc
        self._ensure_audio(out_path)
        return FFmpegProcessor.probe_duration(out_path)

    @staticmethod
    def _silent_fallback(text: str, out_path: str) -> None:
        words = max(1, len(text.split()))
        duration = max(8.0, words / 2.5)  # ~2.5 từ/giây
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=24000:cl=mono",
                "-t",
                f"{duration:.2f}",
                "-c:a",
                "libmp3lame",
                out_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

    @staticmethod
    def _ensure_audio(path: str) -> None:
        if not os.path.exists(path) or os.path.getsize(path) <= 0:
            raise RenderError(f"TTS không tạo được file audio hợp lệ: {path}")

