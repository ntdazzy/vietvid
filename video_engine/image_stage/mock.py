"""Mock image provider — test pipeline không tốn tiền: copy ảnh nguồn hoặc vẽ placeholder."""

from __future__ import annotations

import os
import shutil

from core.logger import logger


class MockImageProvider:
    name = "mock"

    def generate(
        self,
        *,
        prompt: str,
        out_path: str,
        input_image_paths: list[str] | None = None,
    ) -> str:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        source = next(
            (p for p in (input_image_paths or []) if p and os.path.exists(p)), None
        )
        if source:
            shutil.copyfile(source, out_path)
        else:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (768, 1024), (24, 32, 48))
            draw = ImageDraw.Draw(img)
            draw.text((30, 480), (prompt or "mock image")[:60], fill=(220, 226, 240))
            img.save(out_path)
        logger.info(f"[image-stage] mock ảnh → {out_path}")
        return out_path
