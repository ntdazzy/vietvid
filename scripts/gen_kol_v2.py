"""KOL faces v2 — Flux 1.1 Pro ULTRA + raw mode để mặt NGƯỜI THẬT, bớt "nét AI".

raw=true → ảnh ít xử lý, giống ảnh chụp đời thường (autovis-style). Prompt nhấn "người
bình thường, không phải người mẫu", da thật có khuyết điểm, biểu cảm tự nhiên, không bóng nhựa.
Ghi đè apps/web/public/kol/<name>.jpg
"""

from __future__ import annotations

import os

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "_fal_key.txt")
OUT = os.path.join(ROOT, "apps", "web", "public", "kol")
FAL_URL = "https://fal.run/fal-ai/flux-pro/v1.1-ultra"

# Ép "ảnh thật người thường", chống vẻ AI bóng-nhựa.
REAL = (
    "real candid photo of an ordinary everyday person, NOT a model, average natural looks, "
    "authentic imperfect skin with visible pores freckles and slight blemishes, natural asymmetric face, "
    "flyaway hair strands, relaxed unposed natural expression, soft available light, "
    "shot on an old iPhone, slight motion blur and noise, documentary snapshot, "
    "no makeup or very minimal, no retouch, no beauty filter, no smooth plastic skin, no studio lighting, "
    "true to life, believable real human"
)

KOL = [
    ("linh", "a Vietnamese woman about 23, casual oversized tee, long dark hair slightly messy, browsing in a "
             "small clothing shop, looking slightly off-camera with a soft natural half-smile"),
    ("mai", "a Vietnamese woman about 26 in a plain bathroom with a small mirror, holding a skincare bottle "
            "loosely, mid morning routine, tired but content natural expression, soft window light"),
    ("an", "a Vietnamese man about 27, plain shirt, sitting in a normal coffee shop holding his phone, "
           "glancing up naturally, ordinary friendly face, a bit of stubble"),
    ("hoa", "a Vietnamese woman about 31 in a lived-in home kitchen, casual clothes, holding a mug, "
            "warm genuine candid laugh caught mid-moment"),
    ("khoa", "a Vietnamese man about 22, hoodie, in his bedroom with shelves behind, casual relaxed look "
             "at the camera, ordinary student vibe"),
    ("thu", "a Vietnamese woman about 35, simple blouse, in a small office, warm approachable natural smile, "
            "real mature skin, everyday professional"),
]


def _key() -> str:
    return open(KEY_FILE, encoding="utf-8").read().strip()


def main() -> None:
    key = _key()
    os.makedirs(OUT, exist_ok=True)
    with httpx.Client() as client:
        for name, prompt in KOL:
            body = {
                "prompt": f"{prompt}. {REAL}",
                "aspect_ratio": "3:4",
                "raw": True,
                "num_images": 1,
                "output_format": "jpeg",
                "safety_tolerance": "3",
            }
            r = client.post(FAL_URL, headers={"Authorization": f"Key {key}"}, json=body, timeout=120)
            r.raise_for_status()
            img = client.get(r.json()["images"][0]["url"], timeout=120).content
            out = os.path.join(OUT, f"{name}.jpg")
            with open(out, "wb") as f:
                f.write(img)
            print(f"  ✓ public/kol/{name}.jpg ({len(img) // 1024}KB)")


if __name__ == "__main__":
    main()
