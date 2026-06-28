"""Thư viện casting KOL — nhiều gương mặt AI thật theo category (Flux Ultra + raw).

Ghi apps/web/public/kol/lib/<id>.jpg để dùng làm "mẫu gương mặt" trong phòng casting.
"""

from __future__ import annotations

import os

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "_fal_key.txt")
OUT = os.path.join(ROOT, "apps", "web", "public", "kol", "lib")
FAL_URL = "https://fal.run/fal-ai/flux-pro/v1.1-ultra"

REAL = (
    "real candid photo of an ordinary everyday Vietnamese person, NOT a model, natural looks, "
    "authentic imperfect skin with visible pores, natural asymmetric face, flyaway hair, "
    "relaxed natural expression, soft available light, shot on a phone, slight grain, "
    "no heavy makeup, no retouch, no plastic skin, no studio lighting, believable real human"
)

LIB = [
    ("tt-nu1", "a Vietnamese woman ~23 in trendy streetwear standing on a city street, fashion blogger vibe"),
    ("tt-nam1", "a Vietnamese man ~25 in stylish casual menswear on an urban street, street style"),
    ("my-nu1", "a Vietnamese woman ~26 with soft natural makeup holding a small cosmetic near a bright vanity"),
    ("my-nu2", "a Vietnamese woman ~24 with fresh dewy skin in a bathroom doing a morning skincare routine"),
    ("fb-nu1", "a Vietnamese girl ~22 in a cozy cafe holding a drink, food vlogger, warm bokeh"),
    ("fb-nam1", "a Vietnamese man ~28 at a street food stall, casual, friendly foodie"),
    ("gym-nam1", "an athletic Vietnamese man ~27 in gym wear inside a gym, mild sweat"),
    ("gym-nu1", "a fit Vietnamese woman ~25 in activewear in a yoga studio, natural"),
    ("vp-nu1", "a Vietnamese woman ~30 in a small office wearing a smart blouse, professional warm smile"),
    ("genz-nu1", "a Gen Z Vietnamese girl ~20 in a colorful trendy outfit in her bedroom, playful"),
    ("cc-nu1", "an elegant Vietnamese woman ~32 in upscale minimal outfit, calm refined look"),
    ("gd-nu1", "a friendly Vietnamese woman ~31 in a lived-in home kitchen holding a mug, warm laugh"),
]


def main() -> None:
    key = open(KEY_FILE, encoding="utf-8").read().strip()
    os.makedirs(OUT, exist_ok=True)
    with httpx.Client() as client:
        for cid, prompt in LIB:
            body = {"prompt": f"{prompt}. {REAL}", "aspect_ratio": "3:4", "raw": True,
                    "num_images": 1, "output_format": "jpeg", "safety_tolerance": "3"}
            r = client.post(FAL_URL, headers={"Authorization": f"Key {key}"}, json=body, timeout=120)
            r.raise_for_status()
            img = client.get(r.json()["images"][0]["url"], timeout=120).content
            with open(os.path.join(OUT, f"{cid}.jpg"), "wb") as f:
                f.write(img)
            print(f"  ✓ public/kol/lib/{cid}.jpg ({len(img) // 1024}KB)")


if __name__ == "__main__":
    main()
