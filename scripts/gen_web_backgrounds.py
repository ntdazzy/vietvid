"""Sinh ảnh NỀN/bối cảnh cho web (cinematic, KHÔNG kiểu AI-gradient tím) qua fal Flux 1.1 Pro.

Nền chụp thật (studio/bàn creator), tối, ánh sáng mềm → thêm chiều sâu mà không "lộ AI".
Ảnh nền → apps/web/public/bg/<key>.jpg
"""

from __future__ import annotations

import os

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "_fal_key.txt")
OUT = os.path.join(ROOT, "apps", "web", "public", "bg")
FAL_URL = "https://fal.run/fal-ai/flux-pro/v1.1"

REAL = (
    "cinematic photograph, photorealistic, soft natural lighting, atmospheric haze, "
    "subtle film grain, shallow depth of field, premium editorial mood, no text, no watermark, "
    "no people, dark moody tones, true-to-life, NOT a 3d render, NOT a flat gradient"
)

BG = [
    ("studio", "an empty dark film studio backdrop, deep charcoal seamless wall, one soft violet rim "
               "light grazing from the side, faint atmospheric haze, cinematic product-shoot mood"),
    ("desk", "moody overhead view of a content creator desk at night, a smartphone on a small tripod, "
             "soft warm key light, dark surface, cozy bokeh in background, premium workspace"),
    ("ring", "a softbox and ring light glowing softly in a dark studio, large warm bokeh circles, "
             "deep shadows, cinematic creator setup, premium and minimal"),
    ("city", "a softly blurred night city street with warm bokeh storefront lights, dark cinematic "
             "tones, golden and violet hues, empty, dreamy background plate"),
]


def _key() -> str:
    return open(KEY_FILE, encoding="utf-8").read().strip()


def main() -> None:
    key = _key()
    os.makedirs(OUT, exist_ok=True)
    with httpx.Client() as client:
        for name, prompt in BG:
            body = {"prompt": f"{prompt}, {REAL}", "image_size": {"width": 1344, "height": 768},
                    "num_images": 1, "output_format": "jpeg", "safety_tolerance": "3"}
            r = client.post(FAL_URL, headers={"Authorization": f"Key {key}"}, json=body, timeout=120)
            r.raise_for_status()
            img = client.get(r.json()["images"][0]["url"], timeout=120).content
            out = os.path.join(OUT, f"{name}.jpg")
            with open(out, "wb") as f:
                f.write(img)
            print(f"  ✓ public/bg/{name}.jpg ({len(img) // 1024}KB)")


if __name__ == "__main__":
    main()
