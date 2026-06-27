"""film_recap — module review phim (mode='film_recap', in-repo, độc lập với affiliate).

P0: source_mode='reupload' single-pass (9:16 blur-pad + caption ASS từ ASR, GIỮ audio gốc).
recap (kịch bản gốc + giọng mới) = P1. Ngân sách RIÊNG (provider='film_recap').
"""
from video_engine.film_recap.runner import render_film_recap

__all__ = ["render_film_recap"]
