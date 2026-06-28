"""Sinh ảnh landing (KOL mặt người thật + nội dung đa chủ đề) qua fal.ai Flux 1.1 Pro.

Đọc khoá từ _fal_key.txt (gitignored). Prompt tối ưu cho "ẢNH NGƯỜI THẬT, KHÔNG LỘ AI":
phong cách ảnh chụp đời thường/điện thoại, da có texture thật (lỗ chân lông, không nhẵn nhựa),
ánh sáng tự nhiên, KHÔNG retouch/CGI/8k/hyperreal (mấy từ đó kéo về vẻ AI-bóng).

Chạy:  PYTHONUTF8=1 python -m scripts.gen_landing_images
Ảnh KOL → apps/web/public/kol/<name>.jpg ; ảnh chủ đề → apps/web/public/samples/<key>.png
"""

from __future__ import annotations

import os
import sys

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILE = os.path.join(ROOT, "_fal_key.txt")
PUB = os.path.join(ROOT, "apps", "web", "public")
FAL_URL = "https://fal.run/fal-ai/flux-pro/v1.1"

# Đuôi chung ép realism + chống "vẻ AI".
REAL = (
    "candid amateur smartphone photo, photorealistic, real natural skin texture with visible pores "
    "and subtle imperfections, soft natural daylight, true-to-life colors, slight film grain, "
    "shot on iPhone, authentic UGC style, NOT retouched, NOT airbrushed, no plastic skin, no CGI, "
    "no 3d render, ordinary believable real person"
)

# Chân dung KOL (mặt người Việt thật) — 3:4.
KOL = [
    ("linh", "portrait of a real Vietnamese woman around 22 years old, long black hair, casual chic "
             "outfit, warm friendly smile, standing in a bright clothing store, fashion blogger vibe"),
    ("mai", "portrait of a real Vietnamese woman around 24, soft natural makeup, holding a skincare "
            "serum bottle near her face, gentle smile, cozy bathroom with warm light, beauty reviewer"),
    ("an", "portrait of a real Vietnamese man around 26, short neat hair, casual shirt, holding a "
           "smartphone showing to camera, relaxed confident expression, modern desk setup, tech reviewer"),
    ("hoa", "portrait of a friendly Vietnamese woman around 30 in a bright modern kitchen, casual "
            "apron, holding a kitchen gadget, cheerful approachable smile, home-goods reviewer"),
]

# Nội dung đa chủ đề (người + sản phẩm, đời thường) — 9:16.
THEMES = [
    ("kol_review", "a young Vietnamese woman sitting on a sofa talking to camera while holding a "
                   "cosmetic product, casual home vlog, natural light from window, full body to waist"),
    ("lookbook", "a young Vietnamese woman in a stylish autumn outfit posing casually on a city "
                 "street, fashion lookbook, candid street style photo, golden hour"),
    ("unboxing", "a Vietnamese man opening a product box at a wooden desk, excited expression, "
                 "phone-filmed unboxing video frame, warm indoor light"),
    ("food_review", "a Vietnamese girl holding a cup of bubble milk tea smiling at camera in a cozy "
                    "cafe, food review vlog frame, warm bokeh background"),
    ("skincare", "close shot of a Vietnamese woman applying skincare in front of a mirror, morning "
                 "routine vlog, soft natural bathroom light, realistic"),
    ("trend", "a young Vietnamese woman doing a casual dance trend in her bedroom, mid-motion, "
              "phone camera, fun energetic, natural light"),
]


def _read_key() -> str:
    if not os.path.exists(KEY_FILE):
        sys.exit(f"Thiếu {KEY_FILE} — dán khoá fal.ai vào file đó (1 dòng).")
    return open(KEY_FILE, encoding="utf-8").read().strip()


def _gen(client: httpx.Client, key: str, prompt: str, size, out: str) -> None:
    body = {"prompt": f"{prompt}, {REAL}", "image_size": size, "num_images": 1,
            "output_format": "jpeg", "safety_tolerance": "3"}
    r = client.post(FAL_URL, headers={"Authorization": f"Key {key}"}, json=body, timeout=120)
    r.raise_for_status()
    url = r.json()["images"][0]["url"]
    img = client.get(url, timeout=120).content
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(img)
    print(f"  ✓ {os.path.relpath(out, ROOT)} ({len(img) // 1024}KB)")


def main() -> None:
    key = _read_key()
    with httpx.Client() as client:
        print("=== KOL portraits (3:4) ===")
        for name, prompt in KOL:
            _gen(client, key, prompt, "portrait_4_3", os.path.join(PUB, "kol", f"{name}.jpg"))
        print("=== Theme content (9:16) ===")
        for keyname, prompt in THEMES:
            _gen(client, key, prompt, {"width": 768, "height": 1344},
                 os.path.join(PUB, "samples", f"{keyname}.png"))
    print("Xong. Ảnh ở apps/web/public/kol + /samples.")


if __name__ == "__main__":
    main()
