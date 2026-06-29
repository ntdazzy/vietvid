"""Sinh ảnh REDESIGN UI theo hướng CHÂN THỰC (candid), KHÔNG "AI bóng nhựa".

Dùng Flux 1.1 Pro ULTRA + raw=true (công thức đã trị model-hoá ở thư viện KOL).
Người = ảnh đời thường, da có khuyết điểm, chụp điện thoại, không retouch. Vật/nền = ảnh thật.
Ra: apps/web/public/showcase/<key>.jpg
"""

from __future__ import annotations

import os

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "_fal_key.txt")
OUT = os.path.join(ROOT, "apps", "web", "public", "showcase")
FAL_URL = "https://fal.run/fal-ai/flux-pro/v1.1-ultra"

# Người THẬT, không model — chống "AI quá".
REAL_PEOPLE = (
    "real candid photo of an ordinary everyday Vietnamese person, NOT a model, natural looks, "
    "authentic imperfect skin with visible pores, natural asymmetric face, flyaway hair, relaxed "
    "natural expression, soft available light, shot on a phone, slight grain, fully clothed, "
    "tasteful, no heavy makeup, no retouch, no plastic skin, no studio glamour, no text, no watermark, "
    "NOT a 3d render, believable real human"
)
# Vật/sản phẩm THẬT.
REAL_OBJ = (
    "real photograph, natural light, authentic, slight real-world imperfections, subtle grain, "
    "shot on a phone or dslr, no CGI, no 3d render, no plastic look, no text, no watermark"
)
# Nền (không người).
REAL_BG = (
    "real candid photograph of a real space, no people, soft natural light, atmospheric, slight grain, "
    "no text, no watermark, NOT a 3d render, NOT a flat gradient, dark moody premium tones"
)

PEOPLE = [
    ("affiliate", "a Vietnamese woman about 25 in smart-casual clothes holding a small skincare bottle toward a phone camera in a bright everyday living room, casual UGC review selfie vibe"),
    ("kol", "a Vietnamese content-creator woman about 24 sitting in front of a small ring light at home, looking at the camera, simple casual top, plain room"),
    ("trend", "a Vietnamese Gen-Z woman about 21 walking on a city street at dusk in trendy autumn streetwear, candid mid-step, blurred street behind"),
    ("explainer", "a Vietnamese man about 28 at a tidy home desk talking to a phone camera, laptop and a notebook, friendly everyday creator"),
    ("lookbook", "a Vietnamese woman about 26 in a neutral-tone minimal outfit standing against a plain beige wall, simple casual fashion snapshot"),
    ("shortfilm", "a lone Vietnamese young man standing by a rain-streaked window at night, quiet moody cinematic candid, real film still"),
]
OBJECTS = [
    ("product", "a wristwatch resting on a wooden table near a window, natural daylight, real product photo with soft reflections"),
    ("food", "a plate of Vietnamese food next to an iced coffee on a small cafe table, overhead view, natural daylight, real cafe snapshot"),
]
BG = [
    ("hero-create", "a cozy content-creator corner at night, a phone on a small tripod lit by a soft warm lamp, lived-in room"),
    ("hero-studio", "an empty simple photo-studio corner with one softbox and a dark seamless wall, faint haze"),
]


def _gen(client: httpx.Client, key: str, name: str, prompt: str, real: str, ar: str) -> None:
    body = {"prompt": f"{prompt}. {real}", "aspect_ratio": ar, "raw": True,
            "num_images": 1, "output_format": "jpeg", "safety_tolerance": "3"}
    r = client.post(FAL_URL, headers={"Authorization": f"Key {key}"}, json=body, timeout=180)
    r.raise_for_status()
    img = client.get(r.json()["images"][0]["url"], timeout=180).content
    with open(os.path.join(OUT, f"{name}.jpg"), "wb") as f:
        f.write(img)
    print(f"  ✓ public/showcase/{name}.jpg ({len(img) // 1024}KB)")


def main() -> None:
    key = open(KEY_FILE, encoding="utf-8").read().strip()
    os.makedirs(OUT, exist_ok=True)
    with httpx.Client() as client:
        for name, prompt in PEOPLE:
            _gen(client, key, name, prompt, REAL_PEOPLE, "3:2")
        for name, prompt in OBJECTS:
            _gen(client, key, name, prompt, REAL_OBJ, "3:2")
        for name, prompt in BG:
            _gen(client, key, name, prompt, REAL_BG, "16:9")


if __name__ == "__main__":
    main()
