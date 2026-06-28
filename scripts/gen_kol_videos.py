"""Hover video cho mặt KOL — LTX-Video i2v (rẻ) + ffmpeg nén về web size.

Clip 5s, cử động nhẹ (live portrait). Submit cả loạt vào queue fal (chạy song song),
poll, tải, nén scale 400px / crf 30 / no audio → ~vài trăm KB mỗi clip.
Ghi cạnh ảnh: <path>.jpg → <path>.mp4
"""

from __future__ import annotations

import base64
import os
import subprocess
import time

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = open(os.path.join(ROOT, "_fal_key.txt"), encoding="utf-8").read().strip()
H = {"Authorization": f"Key {KEY}"}
MODEL = "fal-ai/ltx-video"
PROMPT = (
    "a real person, very subtle natural movement, gentle breathing and a slight blink, "
    "tiny head motion, minimal camera motion, photorealistic, stable undistorted face, "
    "seamless looped cinemagraph"
)

PUB = os.path.join(ROOT, "apps", "web", "public", "kol")
JOBS = (
    [os.path.join(PUB, "lib", f"{i}.jpg") for i in
     ["tt-nu1", "tt-nam1", "my-nu1", "my-nu2", "fb-nu1", "fb-nam1",
      "gym-nam1", "gym-nu1", "vp-nu1", "genz-nu1", "cc-nu1", "gd-nu1"]]
    + [os.path.join(PUB, f"{n}.jpg") for n in ["linh", "mai", "an", "hoa"]]
)


def submit(c: httpx.Client, path: str) -> str:
    data = "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()
    r = c.post(f"https://queue.fal.run/{MODEL}/image-to-video", headers=H,
               json={"prompt": PROMPT, "image_url": data})
    r.raise_for_status()
    return r.json()["request_id"]


def main() -> None:
    with httpx.Client(timeout=240) as c:
        pending = {}  # rid -> out_path
        for jpg in JOBS:
            rid = submit(c, jpg)
            pending[rid] = jpg[:-4] + ".mp4"
            print("submitted", os.path.basename(jpg))
        print(f"--- {len(pending)} jobs in queue, polling ---")
        while pending:
            for rid in list(pending):
                base = f"https://queue.fal.run/{MODEL}/requests/{rid}"
                try:
                    st = c.get(base + "/status", headers=H).json().get("status")
                except httpx.HTTPError:
                    continue
                if st == "COMPLETED":
                    out = pending.pop(rid)
                    vid = c.get(base, headers=H).json().get("video", {}).get("url")
                    if not vid:
                        print("  no video for", out); continue
                    raw = out + ".raw.mp4"
                    with open(raw, "wb") as f:
                        f.write(c.get(vid, timeout=240).content)
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", raw, "-vf", "scale=400:-2",
                         "-c:v", "libx264", "-crf", "30", "-an", "-movflags", "+faststart", out],
                        capture_output=True,
                    )
                    os.remove(raw)
                    kb = os.path.getsize(out) // 1024 if os.path.exists(out) else 0
                    print(f"  ✓ {os.path.relpath(out, ROOT)} ({kb}KB) · {len(pending)} left")
            if pending:
                time.sleep(6)
    print("Xong.")


if __name__ == "__main__":
    main()
