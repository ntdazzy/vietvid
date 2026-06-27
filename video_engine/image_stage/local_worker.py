"""local_worker.py — worker SUBPROCESS sinh ảnh doodle LOCAL bằng SDXL (+LoRA) trên GPU (Pha B).

Chạy như tiến trình con của LocalImageProvider: load model 1 LẦN → đọc yêu cầu JSON từng dòng qua STDIN
→ sinh ảnh → ghi kết quả JSON qua STDOUT. Tiến trình CHẾT = CUDA tự giải phóng VRAM (không pin GPU lúc
MoviePy/ffmpeg render). Transport stdin/stdout JSON (đơn giản, không HTTP/queue nặng — né nghẽn Windows).

Cấu hình qua ENV (không nhét registry — tuning thử nghiệm):
  LONGFORM_SDXL_MODEL  (base, mặc định stabilityai/stable-diffusion-xl-base-1.0)
  LONGFORM_SDXL_LORA   (repo/path LoRA phong cách doodle; rỗng = chỉ base + prompt phẳng)
  LONGFORM_SDXL_LORA_W (alpha LoRA, mặc định 0.8) · LONGFORM_SDXL_TRIGGER (trigger word của LoRA)
  LONGFORM_SDXL_STEPS  (số bước, mặc định 26)
"""

import json
import os
import re
import sys
from collections import deque
from pathlib import Path

# Prompt phẳng + negative ÉP bỏ "nét AI" (gradient/bóng/3D) — bài học STYLE_PREFIX + Stage 5.
_NEG = (
    "background, text, watermark, collage, repeated object, multiple objects, pattern, extra marks, "
    "pair, two, duplicate, duplicated subject, second object, "
    "swirl, splash, shadow, drop shadow, realistic, photo, stock image, 3d, gradient, shading, dark, "
    "sketch, pencil sketch, ink sketch, crosshatching, hatching, scratchy pen lines, detailed texture, "
    "realistic product drawing, product render, rigid geometry, vector icon, stiff pose, room"
)
_OBJECT_ONLY_NEG = "person, face, head, body, portrait, human, man, woman, shoulders, torso, neck, ears, eyes, nose, mouth"
# NGẮN GỌN + đặt SAU subject (subject phải dẫn token đầu để SDXL bám nội dung — fix "ảnh nào cũng 1 cô gái"
# do style dài đè subject). Giữ flat/viền-đậm/nền-trắng nhưng không nuốt prompt subject.
_STYLE_HEAD = "single centered cutout on pure white background"
_STYLE_TAIL = (
    "bright flat color fills, thick wobbly black outline, playful rounded doodle, "
    "loose organic shape, simple details, no glossy, no text"
)
_ICON_RE = re.compile(r"\bicons?\b", re.IGNORECASE)
_STYLE_MARKER_RE = re.compile(
    r"\b(one single simple hand-drawn subject|soft playful uneven outline|clear bright flat colors|"
    r"large centered|natural non-rigid shape|no stiff vector icon|no square or circle geometric construction|"
    r"plain pure white background|single centered cutout|colorful flat colors|wobbly uneven black outline|"
    r"soft hand-drawn doodle|no glossy render)\b",
    re.IGNORECASE,
)
_SUBJECT_ALIASES = (
    (re.compile(r"\b(soccer player|football player|player)\b.*\b(soccer ball|football ball)\b", re.IGNORECASE), "one full body soccer player kicking a soccer ball"),
    (re.compile(r"\b(soccer goal|football goal)\b.*\b(goalkeeper|goalie)\b", re.IGNORECASE), "one soccer goal with red posts, net, green grass patch, and goalkeeper"),
    (re.compile(r"\b(soccer goal|football goal)\b.*\bnet\b", re.IGNORECASE), "one soccer goal with red posts, net, and green grass patch"),
    (re.compile(r"\b(soccer goalkeeper|football goalkeeper|goalkeeper|goalie)\b", re.IGNORECASE), "one full body soccer goalkeeper with gloves"),
    (re.compile(r"\b(purple sneaker|sneaker|shoe)\b", re.IGNORECASE), "simple bright cartoon purple sneaker shoe alone"),
    (re.compile(r"\b(blue backpack|backpack|school bag|rucksack)\b", re.IGNORECASE), "simple bright cartoon blue backpack alone, no person"),
    (re.compile(r"\b(red baseball cap|baseball cap|cap|hat)\b", re.IGNORECASE), "simple bright cartoon red baseball cap alone, no face, no head, no person"),
    (re.compile(r"\b(green water bottle|water bottle|bottle)\b", re.IGNORECASE), "simple bright cartoon green water bottle alone, tall bottle shape"),
    (re.compile(r"\b(yellow skateboard|skateboard)\b", re.IGNORECASE), "simple bright cartoon yellow skateboard alone, horizontal board with wheels"),
    (re.compile(r"\b(birthday cake with candles|birthday cake|cake with candles)\b", re.IGNORECASE), "simple bright cartoon birthday cake with candles"),
    (re.compile(r"\b(whistle|referee whistle|sports whistle)\b", re.IGNORECASE), "referee whistle"),
    (re.compile(r"\b(open book|book icon|book)\b", re.IGNORECASE), "open book"),
    (re.compile(r"\b(gold trophy|golden trophy cup|trophy cup|trophy)\b", re.IGNORECASE), "gold trophy"),
    (re.compile(r"\b(goalkeeper glove|goalie glove|glove)\b", re.IGNORECASE), "goalkeeper glove"),
    (re.compile(r"\b(soccer ball|football ball)\b", re.IGNORECASE), "soccer ball"),
)
_PRODUCT_REF_RE = re.compile(
    r"\b(extract only|e-commerce|product|apparel|fabric|logo|preserve the exact identity)\b",
    re.IGNORECASE,
)
_PERSON_REF_RE = re.compile(
    r"\b(person|man|woman|boy|girl|face|head|portrait|avatar|character|footballer|soccer player|football player|player|goalkeeper|goalie|athlete)\b|người|cầu thủ|cau thu|nguoi",
    re.IGNORECASE,
)
_FULL_BODY_RE = re.compile(
    r"\b(full body|whole body|entire body|head to toe)\b|toàn thân|toan than",
    re.IGNORECASE,
)


_NO_FULL_BODY_RE = re.compile(r"\b(no|not|without)\s+full[- ]body\b|\bno\s+full\s+body\b", re.IGNORECASE)


def _wants_full_body(prompt: str) -> bool:
    text = str(prompt or "")
    if _NO_FULL_BODY_RE.search(text):
        return False
    return bool(_FULL_BODY_RE.search(text))


def _negative_prompt(prompt: str) -> str:
    text = str(prompt or "")
    lower = text.lower()
    if ("soccer goal" in lower or "football goal" in lower) and "goalkeeper" not in lower and "goalie" not in lower:
        return f"{_NEG}, {_OBJECT_ONLY_NEG}, soccer ball, football ball, ball, multiple goals, repeated goal"
    if ("soccer goal" in lower or "football goal" in lower) and ("goalkeeper" in lower or "goalie" in lower):
        return f"{_NEG}, soccer ball, football ball, ball, multiple goals, repeated goal"
    if _PERSON_REF_RE.search(text) or _wants_full_body(text):
        return _NEG
    return f"{_NEG}, {_OBJECT_ONLY_NEG}"


def _subject_prompt(text: str) -> str:
    subject = " ".join(str(text or "").split())
    if not subject:
        return ""
    subject = " ".join(_ICON_RE.sub(" ", subject).split())
    subject = _STYLE_MARKER_RE.split(subject, maxsplit=1)[0].strip(" ,")
    for pattern, replacement in _SUBJECT_ALIASES:
        if pattern.search(subject):
            subject = replacement
            break
    if not re.search(r"\b(one|single|1)\b", subject, flags=re.IGNORECASE):
        subject = f"one {subject}"
    return f"{subject}, only that subject, no pair, no duplicate"


def _whiten_background(img):
    """Make light neutral background pixels connected to image edges pure white."""
    try:
        import numpy as np
        from PIL import Image

        arr = np.array(img.convert("RGB"), dtype=np.uint8)
        h, w = arr.shape[:2]
        rgb = arr.astype(np.int16)
        mean = rgb.mean(axis=2)
        spread = rgb.max(axis=2) - rgb.min(axis=2)
        candidate = (mean >= 150) & (spread <= 65)
        seen = np.zeros((h, w), dtype=bool)
        q = deque()

        for x in range(w):
            for y in (0, h - 1):
                if candidate[y, x] and not seen[y, x]:
                    seen[y, x] = True
                    q.append((x, y))
        for y in range(h):
            for x in (0, w - 1):
                if candidate[y, x] and not seen[y, x]:
                    seen[y, x] = True
                    q.append((x, y))

        while q:
            x, y = q.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and candidate[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((nx, ny))

        if seen.mean() > 0.03:
            arr[seen] = 255
        edge = max(2, min(h, w) // 100)
        arr[:edge, :] = 255
        arr[-edge:, :] = 255
        arr[:, :edge] = 255
        arr[:, -edge:] = 255
        return Image.fromarray(arr)
    except Exception:
        return img


def _paper_background(img):
    try:
        import numpy as np
        from PIL import Image

        arr = np.array(img.convert("RGB")).astype(np.int16)
        h, w = arr.shape[:2]
        mean = arr.mean(axis=2)
        spread = arr.max(axis=2) - arr.min(axis=2)
        candidate = (mean >= 235) & (spread <= 28)
        seen = np.zeros((h, w), dtype=bool)
        q = deque()
        for x in range(w):
            for y in (0, h - 1):
                if candidate[y, x] and not seen[y, x]:
                    seen[y, x] = True
                    q.append((x, y))
        for y in range(h):
            for x in (0, w - 1):
                if candidate[y, x] and not seen[y, x]:
                    seen[y, x] = True
                    q.append((x, y))
        while q:
            x, y = q.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and candidate[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((nx, ny))
        if seen.mean() < 0.03:
            return img
        yy, xx = np.indices((h, w))
        grain = (((xx * 3 + yy * 5) % 13) - 6).astype(np.int16)
        paper = np.zeros_like(arr)
        paper[:, :, 0] = np.clip(247 + grain, 236, 255)
        paper[:, :, 1] = np.clip(248 + grain, 236, 255)
        paper[:, :, 2] = np.clip(244 + grain, 234, 255)
        arr[seen] = paper[seen]
        return Image.fromarray(arr.clip(0, 255).astype("uint8"))
    except Exception:
        return img


def _polish_colors(img):
    try:
        import numpy as np
        from PIL import Image, ImageEnhance, ImageOps

        img = ImageEnhance.Color(img).enhance(1.08)
        img = ImageEnhance.Contrast(img).enhance(1.04)
        img = ImageEnhance.Brightness(img).enhance(1.02)
        img = _whiten_background(ImageOps.posterize(img, 5))
        arr = np.array(img.convert("RGB")).astype(np.int16)
        mean = arr.mean(axis=2)
        spread = arr.max(axis=2) - arr.min(axis=2)
        vivid = (mean > 55) & (mean < 235) & (spread > 90)
        arr[vivid] = np.clip(arr[vivid] * 0.82 + 20, 0, 255)
        highlight = (mean > 165) & (mean < 245) & (spread > 28)
        arr[highlight] = np.clip(arr[highlight] * 0.86 + 18, 0, 255)
        paper = (mean > 225) & (spread < 20)
        yy, xx = np.indices(mean.shape)
        texture = (((xx * 3 + yy * 5) % 11) - 5).astype(np.int16)
        for channel in range(3):
            arr[:, :, channel][paper] = np.clip(arr[:, :, channel][paper] + texture[paper], 232, 255)
        img = Image.fromarray(arr.astype("uint8"))
        return _whiten_background(img)
    except Exception:
        return img


def _reference_image(path: str):
    from PIL import Image

    src = Image.open(path).convert("RGB")
    src.thumbnail((_SIZE, _SIZE), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (_SIZE, _SIZE), (255, 255, 255))
    canvas.paste(src, ((_SIZE - src.width) // 2, (_SIZE - src.height) // 2))
    return canvas


def _alpha_bbox(img):
    try:
        import numpy as np

        alpha = np.array(img.getchannel("A"))
        try:
            import cv2

            mask = (alpha > 24).astype(np.uint8)
            total_area = int(mask.sum())
            count, labels, stats, _centers = cv2.connectedComponentsWithStats(mask, 8)
            best = None
            best_score = -1
            for idx in range(1, count):
                x, y, w, h, area = (int(v) for v in stats[idx])
                if area < max(80, int(total_area * 0.01)) or w < 8 or h < 8:
                    continue
                aspect = w / max(1, h)
                if aspect > 3.2 or aspect < 0.16:
                    continue
                score = area * (1.4 if 0.35 <= aspect <= 1.8 else 1.0)
                if score > best_score:
                    best = (x, y, x + w, y + h)
                    best_score = score
            if best:
                x0, y0, x1, y1 = best
                pad = max(8, int(max(x1 - x0, y1 - y0) * 0.12))
                return (
                    max(0, x0 - pad),
                    max(0, y0 - pad),
                    min(img.width, x1 + pad),
                    min(img.height, y1 + pad),
                )
        except Exception:
            pass
        ys, xs = np.where(alpha > 24)
        if len(xs) < 20 or len(ys) < 20:
            return None
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        w, h = max(1, x1 - x0), max(1, y1 - y0)
        if w / h > 2.8:
            cx = (x0 + x1) // 2
            half = int(h * 1.25)
            x0, x1 = max(0, cx - half), min(img.width, cx + half)
        pad = max(8, int(max(x1 - x0, y1 - y0) * 0.08))
        return (
            max(0, x0 - pad),
            max(0, y0 - pad),
            min(img.width, x1 + pad),
            min(img.height, y1 + pad),
        )
    except Exception:
        return None


def _remove_ref_background(img):
    if os.getenv("LONGFORM_SDXL_REF_REMOVE_BG", "1").strip().lower() in {"0", "false", "no"}:
        return img
    try:
        from rembg import remove

        cut = remove(img)
        return cut if hasattr(cut, "getchannel") else img
    except Exception:
        return img


def _prepare_reference_cutout(img):
    try:
        import numpy as np
        from PIL import Image

        src = img.convert("RGBA")
        alpha = np.array(src.getchannel("A"))
        if (alpha < 250).any():
            return src
        rgba = np.array(src)
        rgb = rgba[:, :, :3].astype(np.int16)
        border = np.concatenate((rgb[:8, :, :].reshape(-1, 3), rgb[-8:, :, :].reshape(-1, 3),
                                 rgb[:, :8, :].reshape(-1, 3), rgb[:, -8:, :].reshape(-1, 3)), axis=0)
        border_light = border.mean(axis=1) >= 245
        border_flat = (border.max(axis=1) - border.min(axis=1)) <= 14
        full_light = rgb.mean(axis=2) >= 245
        full_flat = (rgb.max(axis=2) - rgb.min(axis=2)) <= 14
        if float((border_light & border_flat).mean()) >= 0.40 or float((full_light & full_flat).mean()) >= 0.22:
            mask = (rgb.mean(axis=2) < 248) | ((rgb.max(axis=2) - rgb.min(axis=2)) > 12)
            rgba[:, :, 3] = (mask.astype(np.uint8) * 255)
            return Image.fromarray(rgba)
        cut = _remove_ref_background(src)
        return cut.convert("RGBA") if hasattr(cut, "convert") else src
    except Exception:
        return img


def _crop_reference_face(img):
    try:
        import numpy as np

        src = img.convert("RGBA")
        box = _alpha_bbox(src)
        if box:
            src = src.crop(box)
        if src.height > src.width * 1.12:
            alpha = np.array(src.getchannel("A")) > 24
            crop_h = max(1, int(src.height * 0.45))
            head_h = max(1, int(src.height * 0.42))
            xs = np.where(alpha[:head_h, :])[1]
            cx = int(np.median(xs)) if len(xs) > 20 else src.width // 2
            crop_w = min(src.width, max(1, int(crop_h * 0.88)))
            x0 = max(0, min(src.width - crop_w, cx - crop_w // 2))
            return src.crop((x0, 0, x0 + crop_w, crop_h))
        try:
            import cv2

            arr = np.array(src.convert("RGB"))
            gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cascade.detectMultiScale(gray, 1.1, 4, minSize=(32, 32))
            if len(faces):
                x, y, w, h = max(faces, key=lambda item: int(item[2]) * int(item[3]))
                pad_x = int(w * 0.70)
                top = int(h * 0.85)
                bottom = int(h * 0.65)
                return src.crop((
                    max(0, x - pad_x),
                    max(0, y - top),
                    min(src.width, x + w + pad_x),
                    min(src.height, y + h + bottom),
                ))
        except Exception:
            pass
        h = src.height
        if h > src.width * 1.12:
            return src.crop((0, 0, src.width, max(1, int(h * 0.48))))
        return src
    except Exception:
        return img


def _drop_tiny_edge_marks(img):
    try:
        import numpy as np
        from PIL import Image

        arr = np.array(img.convert("RGB"))
        rgb = arr.astype(np.int16)
        mask = (rgb.mean(axis=2) < 248) | ((rgb.max(axis=2) - rgb.min(axis=2)) > 12)
        total = int(mask.sum())
        if total < 100:
            return img
        try:
            import cv2

            labels_count, labels, stats, centers = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
            drop = np.zeros(mask.shape, dtype=bool)
            h, w = mask.shape
            for idx in range(1, labels_count):
                area = int(stats[idx, cv2.CC_STAT_AREA])
                cx, cy = centers[idx]
                near_edge = cx < w * 0.16 or cx > w * 0.84 or cy > h * 0.84
                if near_edge and area < max(80, int(total * 0.025)):
                    drop |= labels == idx
            if drop.any():
                arr[drop] = 255
                return Image.fromarray(arr)
        except Exception:
            return img
        return img
    except Exception:
        return img


def _keep_related_generated_parts(prompt: str) -> bool:
    text = str(prompt or "").lower()
    return bool(
        _PERSON_REF_RE.search(text)
        or "goalkeeper" in text
        or "soccer goal" in text
        or "football goal" in text
        or "soccer ball" in text
        or "football ball" in text
    )


def _isolate_generated_subject(img, prompt: str = ""):
    try:
        import numpy as np
        from PIL import Image

        keep_parts = _keep_related_generated_parts(prompt)
        cut = _remove_ref_background(img.convert("RGBA"))
        try:
            import cv2

            alpha = np.array(cut.getchannel("A"))
            mask = (alpha > 24).astype(np.uint8)
            total = int(mask.sum())
            count, labels, stats, _centers = cv2.connectedComponentsWithStats(mask, 8)
            kept = None
            kept_area = 0
            if not keep_parts:
                for idx in range(1, count):
                    x, y, w, h, area = (int(v) for v in stats[idx])
                    if area < max(200, int(total * 0.12)) or w < 24 or h < 24:
                        continue
                    if area > kept_area:
                        kept = idx
                        kept_area = area
                big_parts = [
                    idx for idx in range(1, count)
                    if int(stats[idx, cv2.CC_STAT_AREA]) >= max(200, int(total * 0.12))
                ]
                if kept is not None and len(big_parts) > 1:
                    arr = np.array(cut)
                    arr[:, :, 3] = np.where(labels == kept, arr[:, :, 3], 0).astype(arr.dtype)
                    cut = Image.fromarray(arr)
        except Exception:
            pass
        box = None
        if keep_parts:
            alpha = np.array(cut.getchannel("A"))
            ys, xs = np.where(alpha > 24)
            if len(xs) >= 20 and len(ys) >= 20:
                x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
                pad = max(8, int(max(x1 - x0, y1 - y0) * 0.12))
                box = (
                    max(0, x0 - pad),
                    max(0, y0 - pad),
                    min(cut.width, x1 + pad),
                    min(cut.height, y1 + pad),
                )
        if box is None:
            box = _alpha_bbox(cut)
        if not box:
            return img
        cut = cut.crop(box)
        target = int(_SIZE * 0.80)
        cut.thumbnail((target, target), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (_SIZE, _SIZE), (255, 255, 255, 255))
        canvas.alpha_composite(cut, ((_SIZE - cut.width) // 2, (_SIZE - cut.height) // 2))
        return canvas.convert("RGB")
    except Exception:
        return img


def _stylize_reference(path: str, prompt: str = ""):
    try:
        import numpy as np
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

        face_only = _PERSON_REF_RE.search(str(prompt or "")) and not _wants_full_body(str(prompt or ""))
        raw = ImageOps.exif_transpose(Image.open(path)).convert("RGBA")
        if face_only:
            raw = _crop_reference_face(raw)
        src = _prepare_reference_cutout(raw)
        if face_only:
            src = _crop_reference_face(src)
        box = _alpha_bbox(src)
        if box:
            src = src.crop(box)
        target = int(_SIZE * 0.78)
        scale = min(target / max(1, src.width), target / max(1, src.height))
        if scale > 1.0:
            src = src.resize((max(1, int(src.width * scale)), max(1, int(src.height * scale))), Image.Resampling.LANCZOS)
        else:
            src.thumbnail((target, target), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (_SIZE, _SIZE), (255, 255, 255, 255))
        canvas.alpha_composite(src, ((_SIZE - src.width) // 2, (_SIZE - src.height) // 2))
        rgb = canvas.convert("RGB")

        try:
            import cv2

            arr = np.array(rgb)
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            smooth = cv2.bilateralFilter(bgr, 9, 75, 75)
            gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 60, 145)
            edges = cv2.dilate(edges, np.ones((2, 2), dtype=np.uint8), iterations=1)
            color = Image.fromarray(cv2.cvtColor(smooth, cv2.COLOR_BGR2RGB))
        except Exception:
            color = rgb.filter(ImageFilter.SMOOTH_MORE)
            edges = np.array(color.convert("L").filter(ImageFilter.FIND_EDGES)) > 35
        color = ImageEnhance.Color(color).enhance(1.25)
        color = ImageEnhance.Contrast(color).enhance(1.08)
        color = ImageEnhance.Brightness(color).enhance(1.08)
        color = ImageOps.posterize(color, 4)
        bg = np.array(rgb).astype(np.int16)
        bg_mask = (bg.mean(axis=2) >= 248) & ((bg.max(axis=2) - bg.min(axis=2)) <= 8)
        person_ref = bool(_PERSON_REF_RE.search(str(prompt or "")))
        out = np.array(color).astype(np.int16)
        if not person_ref:
            out[edges > 0] = (18, 18, 18)
        out[bg_mask] = (255, 255, 255)
        result = _whiten_background(Image.fromarray(out.astype("uint8")))
        if face_only:
            result = _drop_tiny_edge_marks(result)
        return result
    except Exception:
        return None


def _load():
    import torch
    from diffusers import StableDiffusionXLPipeline

    model = os.getenv("LONGFORM_SDXL_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    kw = dict(torch_dtype=torch.float16, use_safetensors=True)
    try:
        pipe = StableDiffusionXLPipeline.from_pretrained(model, variant="fp16", **kw)
    except Exception:                       # repo không có variant fp16 → tải bản thường
        pipe = StableDiffusionXLPipeline.from_pretrained(model, **kw)
    pipe = pipe.to("cuda")
    pipe.set_progress_bar_config(disable=True)
    try:                                    # giảm VRAM peak trên 12GB
        pipe.enable_vae_tiling()
    except Exception:
        pass
    lora = os.getenv("LONGFORM_SDXL_LORA", "").strip()
    if lora:
        try:
            lora_path = Path(lora)
            if lora_path.is_dir() and (lora_path / "pytorch_lora_weights.safetensors").exists():
                pipe.load_lora_weights(lora, weight_name="pytorch_lora_weights.safetensors")
            else:
                pipe.load_lora_weights(lora)
            pipe.fuse_lora(lora_scale=float(os.getenv("LONGFORM_SDXL_LORA_W", "0.8")))
            print(json.dumps({"info": f"lora loaded: {lora}"}), flush=True)
        except Exception as exc:
            raise RuntimeError(f"lora load fail: {str(exc)[:140]}") from exc
    return pipe


_SIZE = int(os.getenv("LONGFORM_SDXL_SIZE", "768"))   # 768 (KHÔNG 1024): nhanh hơn ~2× + đỡ VRAM trên 3060


def main():
    import torch

    try:
        pipe = _load()
    except Exception as exc:                # load thất bại → báo fatal để caller dừng rõ lỗi
        print(json.dumps({"fatal": str(exc)[:200]}), flush=True)
        return
    steps = int(os.getenv("LONGFORM_SDXL_STEPS", "20"))
    # WARMUP phải CÙNG CỠ với gen thật (_SIZE): CUDA biên dịch kernel THEO shape → warmup 512 mà gen 1024 thì
    # lần gen đầu PHẢI biên dịch lại → >200s bị kill (lỗi rv25). Warmup đúng cỡ → ảnh thật đầu nhanh.
    try:
        with torch.inference_mode():
            pipe(prompt="a circle", negative_prompt=_NEG, num_inference_steps=2, width=_SIZE, height=_SIZE,
                 generator=torch.Generator("cuda").manual_seed(0))
        torch.cuda.synchronize()
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps({"ready": True}), flush=True)

    trigger = os.getenv("LONGFORM_SDXL_TRIGGER", "").strip()
    img2img_pipe = None
    ref_strength = max(0.15, min(0.9, float(os.getenv("LONGFORM_SDXL_REF_STRENGTH", "0.58"))))
    ref_mode = os.getenv("LONGFORM_SDXL_REF_MODE", "trace").strip().lower()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        if req.get("cmd") == "quit":
            break
        out = req.get("out_path", "")
        seed = int(req.get("seed", 42))
        ref_path = str(req.get("input_image_path") or "").strip()
        # Keep this short: SDXL may ignore the tail when the prompt is too long.
        subject = _subject_prompt(req.get("prompt", ""))
        full = ", ".join(p for p in (subject, _STYLE_HEAD, _STYLE_TAIL, trigger) if p).strip(", ")
        negative = _negative_prompt(req.get("prompt", ""))
        try:
            if ref_path and _PRODUCT_REF_RE.search(str(req.get("prompt", ""))):
                print(json.dumps({"ok": False, "err": "local_ref_not_for_product"}), flush=True)
                continue
            traced_ref = False
            with torch.inference_mode():
                if ref_path and os.path.exists(ref_path):
                    img = _stylize_reference(ref_path, req.get("prompt", "")) if ref_mode in {"trace", "stylize", "cartoonize"} else None
                    traced_ref = img is not None
                    if img is None and img2img_pipe is None:
                        from diffusers import StableDiffusionXLImg2ImgPipeline

                        img2img_pipe = StableDiffusionXLImg2ImgPipeline.from_pipe(pipe)
                        img2img_pipe.set_progress_bar_config(disable=True)
                    if img is None:
                        img = img2img_pipe(
                            prompt=full[:900], image=_reference_image(ref_path), strength=ref_strength,
                            negative_prompt=negative, num_inference_steps=steps, guidance_scale=6.0,
                            generator=torch.Generator("cuda").manual_seed(seed),
                        ).images[0]
                else:
                    img = pipe(prompt=full[:900], negative_prompt=negative, num_inference_steps=steps,
                               guidance_scale=6.5, width=_SIZE, height=_SIZE,
                               generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            torch.cuda.synchronize()
            if not (ref_path and os.path.exists(ref_path)):
                img = _isolate_generated_subject(img, req.get("prompt", ""))
            img = _whiten_background(img) if traced_ref else _polish_colors(_whiten_background(img))
            if not (ref_path and os.path.exists(ref_path)):
                img = _isolate_generated_subject(img, req.get("prompt", ""))
            img = _paper_background(img)
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
            img.save(out)
            torch.cuda.empty_cache()
            print(json.dumps({"ok": True, "out_path": out}), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "err": str(exc)[:200]}), flush=True)


if __name__ == "__main__":
    main()
