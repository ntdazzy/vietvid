"""local.py — LocalImageProvider: sinh ảnh doodle bằng SDXL local (Pha B), khớp interface GeminiImageProvider.

Không load diffusers trong tiến trình render (né rò CUDA + tranh VRAM): bắc cầu sang local_worker.py
(subprocess load model 1 lần). Transport stdin/stdout JSON đơn giản. shutdown() giết worker → giải phóng VRAM.
HybridImageProvider: thử local trước, hỏng → Gemini (bảo hiểm chất lượng).

ĐỌC STDOUT CÓ HẠN GIỜ: worker có thể treo (GPU OOM/kẹt). Mọi vòng đọc dùng reader-thread + queue +
timeout — quá hạn → kill worker + trả None để caller báo lỗi rõ, KHÔNG fallback Gemini trong flow chính.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time

from core.logger import logger

_READY_TIMEOUT = 360.0   # chờ worker load model + warmup CUDA lần đầu — quá hạn = coi như chết
# Ảnh đầu có lúc chạm ~247s trên máy này dù đã warmup; 320s tránh kill nhầm ảnh thật.
_GEN_TIMEOUT = 320.0

_SDXL_ENV_KEYS = (
    "LONGFORM_SDXL_MODEL",
    "LONGFORM_SDXL_LORA",
    "LONGFORM_SDXL_LORA_W",
    "LONGFORM_SDXL_TRIGGER",
    "LONGFORM_SDXL_STEPS",
    "LONGFORM_SDXL_SIZE",
    "LONGFORM_SDXL_REF_STRENGTH",
    "LONGFORM_SDXL_REF_MODE",
    "LONGFORM_SDXL_REF_REMOVE_BG",
)

_DETAILED_PROMPT_RE = re.compile(
    r"\b(wearing|holding|using|with|blue jersey|red jersey|green jersey|shirt|áo|ao)\b",
    re.IGNORECASE,
)
_DOODLE_SIMPLE_DETAILED_PROMPTS = {
    "cake with candles",
    "birthday cake with candles",
}
_LOCAL_REF_BLOCK_RE = re.compile(
    r"\b(extract only|e-commerce|product|apparel|fabric|logo|preserve the exact identity)\b",
    re.IGNORECASE,
)
_PERSON_PROMPT_RE = re.compile(
    r"\b(person|man|woman|boy|girl|face|head|portrait|avatar|character|footballer|soccer player|football player|player|athlete)\b|người|cầu thủ|cau thu|nguoi",
    re.IGNORECASE,
)
_RELATED_PARTS_PROMPT_RE = re.compile(
    r"\b(soccer player|football player|goalkeeper|soccer goal|football goal|soccer ball|football ball)\b",
    re.IGNORECASE,
)
_STYLE_REF_PROMPT_RE = re.compile(
    r"\bdraw (?:the object )?in the exact same hand-drawn cartoon art style as the reference image\b",
    re.IGNORECASE,
)
_REAL_REF_PROMPT_RE = re.compile(
    r"\b(recurring presenter|same face, glasses, hairstyle, outfit|person in the reference image)\b",
    re.IGNORECASE,
)
_LOCAL_SUBJECT_SUFFIX_RE = re.compile(
    r"\s+(?:ONE SINGLE|Keep the recurring|IMPORTANT face-only rule:|Regenerate once more:)\b.*$",
    re.IGNORECASE,
)


def _worker_env() -> dict[str, str]:
    env = dict(os.environ, PYTHONUTF8="1", PYTHONUNBUFFERED="1")
    try:
        from dotenv import dotenv_values

        root = Path(__file__).resolve().parents[2]
        values = dotenv_values(root / ".env")
        for key in _SDXL_ENV_KEYS:
            value = values.get(key)
            if value and not str(env.get(key, "")).strip():
                env[key] = str(value)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[local-sdxl] doc .env lora loi: {str(exc)[:140]}")
    return env


def _worker_python() -> str:
    root = Path(__file__).resolve().parents[2]
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    return str(venv_py) if venv_py.exists() else sys.executable


def _local_subject_prompt(prompt: str) -> str:
    if "Subject is:" not in prompt:
        return prompt
    subject = prompt.split("Subject is:", 1)[-1].strip()
    subject = _LOCAL_SUBJECT_SUFFIX_RE.sub("", subject).strip(" ,")
    return subject or prompt


def _local_reference_paths(prompt: str, input_image_paths) -> list[str] | None:
    refs = [p for p in (input_image_paths or []) if p and os.path.exists(p)]
    if not refs:
        return None
    if _STYLE_REF_PROMPT_RE.search(prompt) and _REAL_REF_PROMPT_RE.search(prompt) and len(refs) > 1:
        return refs[1:]
    if _STYLE_REF_PROMPT_RE.search(prompt) and not _REAL_REF_PROMPT_RE.search(prompt):
        return None
    return refs


def _try_doodle_library(prompt: str, out_path: str) -> str | None:
    simple_prompt = re.sub(r"[^a-z0-9 ]+", " ", (prompt or "").lower())
    simple_prompt = re.sub(r"\s+", " ", simple_prompt).strip()
    if _DETAILED_PROMPT_RE.search(prompt or "") and simple_prompt not in _DOODLE_SIMPLE_DETAILED_PROMPTS:
        return None
    try:
        from PIL import Image
        from video_engine.long_narrative.doodle_lib import lookup

        src_path = lookup(prompt)
        if not src_path or not os.path.exists(src_path):
            return None
        size = int(os.getenv("LONGFORM_SDXL_SIZE", "768"))
        img = Image.open(src_path).convert("RGBA")
        img.thumbnail((int(size * 0.78), int(size * 0.78)), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        canvas.alpha_composite(img, ((size - img.width) // 2, (size - img.height) // 2))
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        canvas.save(out_path)
        logger.info(f"[local-sdxl] dùng doodle_lib thay SDXL prompt-only → {out_path}")
        return out_path
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[local-sdxl] doodle_lib fallback lỗi: {str(exc)[:120]}")
        return None


def _erode_mask(mask, radius: int = 2):
    import numpy as np

    padded = np.pad(mask, radius, constant_values=False)
    h, w = mask.shape
    out = np.ones_like(mask, dtype=bool)
    for dy in range(radius * 2 + 1):
        for dx in range(radius * 2 + 1):
            out &= padded[dy:dy + h, dx:dx + w]
    return out


def _component_count(mask, threshold: int) -> int:
    import numpy as np

    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    count = 0
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q = [(x, y)]
            seen[y, x] = True
            area = 0
            while q:
                cx, cy = q.pop()
                area += 1
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        q.append((nx, ny))
            if area >= threshold:
                count += 1
    return count


def _allows_related_parts(prompt: str) -> bool:
    return bool(_RELATED_PARTS_PROMPT_RE.search(prompt or ""))


def _generated_image_issues(path: str, prompt: str = "") -> list[str]:
    try:
        import numpy as np
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        rgba = np.array(img)
        alpha = rgba[:, :, 3]
        if (alpha < 250).any():
            mask = alpha > 10
        else:
            rgb = rgba[:, :, :3].astype(np.int16)
            edge_px = np.concatenate((rgb[:6, :, :].reshape(-1, 3), rgb[-6:, :, :].reshape(-1, 3),
                                      rgb[:, :6, :].reshape(-1, 3), rgb[:, -6:, :].reshape(-1, 3)), axis=0)
            bg = np.median(edge_px, axis=0)
            dist = np.abs(rgb - bg).max(axis=2)
            mask = (dist > 28) & (rgb.mean(axis=2) < 252)
        ys, xs = np.where(mask)
        if not len(xs):
            return ["empty"]
        left, right = int(xs.min()), int(xs.max()) + 1
        top, bottom = int(ys.min()), int(ys.max()) + 1
        bbox_w = right - left
        bbox_h = bottom - top
        area_ratio = (bbox_w * bbox_h) / max(1, img.width * img.height)
        edge = max(2, min(img.size) // 40)
        edge_pixels = (
            int(mask[:edge, :].sum()) + int(mask[-edge:, :].sum()) +
            int(mask[:, :edge].sum()) + int(mask[:, -edge:].sum())
        )
        issues = []
        if area_ratio < 0.05 or bbox_w < img.width * 0.18 or bbox_h < img.height * 0.18:
            issues.append("too_tiny")
        lower_prompt = (prompt or "").lower()
        if "backpack" in lower_prompt and area_ratio < 0.12:
            issues.append("too_tiny")
        if "water bottle" in lower_prompt and bbox_h / max(1, bbox_w) < 1.35:
            issues.append("wrong_bottle_shape")
        if "skateboard" in lower_prompt and bbox_h / max(1, bbox_w) > 1.45:
            issues.append("wrong_skateboard_shape")
        if any(term in lower_prompt for term in ("baseball cap", " cap", "hat")):
            rgb = rgba[:, :, :3].astype(np.int16)
            has_face = False
            try:
                import cv2

                arr = np.array(img.convert("RGB"))
                gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
                cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                faces = cascade.detectMultiScale(gray, 1.05, 3, minSize=(60, 60))
                has_face = len(faces) > 0
            except Exception:
                grey_skin = (
                    mask
                    & (rgb.mean(axis=2) > 70)
                    & (rgb.mean(axis=2) < 210)
                    & ((rgb.max(axis=2) - rgb.min(axis=2)) < 38)
                )
                lower_half = grey_skin[top + int(bbox_h * 0.42):bottom, left:right]
                has_face = int(lower_half.sum()) / max(1, int(mask.sum())) > 0.25
            if has_face:
                issues.append("object_contains_person")
        positive_full_body = re.search(r"\b(whole body|entire body|head to toe)\b", lower_prompt)
        positive_full_body = positive_full_body or (
            "full body" in lower_prompt and "no full body" not in lower_prompt
        )
        if (
            "person in the reference image" in lower_prompt
            and not positive_full_body
        ):
            box = mask[top:bottom, left:right]
            lower_body = box[int(box.shape[0] * 0.70):, :].sum() / max(1, int(box.sum()))
            if bbox_h / max(1, bbox_w) > 1.12 and lower_body > 0.20:
                issues.append("body_in_face_only")
        if (
            not _allows_related_parts(lower_prompt)
            and _component_count(mask, max(200, int(mask.sum() * 0.12))) > 1
        ):
            issues.append("multi_part")
        if _component_count(_erode_mask(mask), max(80, int(mask.sum() * 0.03))) >= 3:
            issues.append("repeated_grid")
        fg = rgba[:, :, :3][mask].astype(np.int16)
        channel_spread = fg.max(axis=1) - fg.min(axis=1)
        fg_mean = fg.mean(axis=1)
        spread = float(channel_spread.mean())
        box = mask[top:bottom, left:right]
        transitions = int((box[:, 1:] != box[:, :-1]).sum() + (box[1:, :] != box[:-1, :]).sum())
        complexity = transitions / max(1, int(box.sum()))
        shape_complexity = transitions / max(1.0, float(box.sum()) ** 0.5)
        if (
            any(term in lower_prompt for term in ("backpack", "bottle", "skateboard"))
            and spread > 78
        ):
            issues.append("icon_color_too_harsh")
        if (
            any(term in lower_prompt for term in ("backpack", "bottle", "skateboard", "football player"))
            and complexity < 0.075
        ):
            issues.append("line_too_smooth")
        black_ratio = float(((fg_mean < 55) & (channel_spread < 45)).mean())
        color_bins = int(len({tuple(row) for row in (fg // 32).astype(np.int16)}))
        light_ratio = float(((fg_mean > 180) & (channel_spread < 75)).mean())
        black_limit = 0.96 if _PERSON_PROMPT_RE.search(lower_prompt) else 0.45
        if black_ratio > black_limit:
            issues.append("too_much_black_outline")
        if _PERSON_PROMPT_RE.search(lower_prompt) and spread < 8 and black_ratio > 0.50:
            issues.append("person_too_mono")
        if color_bins < 24:
            issues.append("too_few_colors")
        if (
            not _PERSON_PROMPT_RE.search(lower_prompt)
            and shape_complexity < 13
            and color_bins < 64
        ):
            issues.append("stiff_icon_risk")
        if (
            not _PERSON_PROMPT_RE.search(lower_prompt)
            and light_ratio > 0.30
            and spread < 52
            and color_bins < 100
        ):
            issues.append("too_pale_stock_like")
        if (
            not _PERSON_PROMPT_RE.search(lower_prompt)
            and spread < 24
            and color_bins < 130
        ):
            issues.append("too_flat_or_product_like")
        edge_gap = min(left, top, img.width - right, img.height - bottom)
        if edge_gap < edge or edge_pixels / max(1, int(mask.sum())) > 0.02:
            issues.append("edge_cut")
        return issues
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[local-sdxl] kiểm ảnh local lỗi: {str(exc)[:120]}")
        return ["check_error"]


def _pad_generated_image(path: str, scale: float = 0.88) -> bool:
    try:
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        w, h = img.size
        small = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        canvas.alpha_composite(small, ((w - small.width) // 2, (h - small.height) // 2))
        canvas.save(path)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[local-sdxl] thêm lề ảnh lỗi: {str(exc)[:120]}")
        return False


class LocalImageProvider:
    name = "local"

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._dead = False          # worker chết khi load → khỏi spawn lại liên tục
        self._q: queue.Queue | None = None

    @staticmethod
    def _pump_stdout(proc, q) -> None:
        """Thread bơm stdout worker vào HÀNG ĐỢI riêng (q truyền vào, không qua self → khỏi race khi respawn).
        Đọc có-hạn-giờ bằng q.get(timeout). EOF/proc chết → sentinel None."""
        try:
            for line in proc.stdout:
                q.put(line)
        except Exception:  # noqa: BLE001
            pass
        q.put(None)

    def _next(self, timeout: float):
        """1 dòng từ worker, tối đa `timeout` giây. None = HẾT GIỜ (treo) hoặc EOF (chết)."""
        try:
            return self._q.get(timeout=max(0.1, timeout))
        except queue.Empty:
            return None

    def _kill_dead(self) -> None:
        """Đánh dấu chết + kill worker (giải phóng GPU) → lần sau khỏi spawn lại."""
        self._dead = True
        p, self._proc = self._proc, None
        if p:
            try:
                p.kill()
            except Exception:  # noqa: BLE001
                pass

    def _ensure(self) -> bool:
        if self._proc and self._proc.poll() is None:
            return True
        if self._dead:
            return False
        worker = os.path.join(os.path.dirname(__file__), "local_worker.py")
        env = _worker_env()
        try:
            self._proc = subprocess.Popen(
                [_worker_python(), worker], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, encoding="utf-8", env=env, bufsize=1)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[local-sdxl] spawn worker lỗi: {str(exc)[:140]}")
            self._dead = True
            return False
        self._q = queue.Queue()
        threading.Thread(target=self._pump_stdout, args=(self._proc, self._q), daemon=True).start()
        # chờ ready CÓ HẠN GIỜ tổng: vòng đọc info/warn, gặp ready → True; fatal/timeout/EOF → kill + False.
        left = _READY_TIMEOUT
        while left > 0:
            t0 = time.monotonic()
            line = self._next(left)
            left -= time.monotonic() - t0
            if line is None:
                logger.warning(f"[local-sdxl] worker KHÔNG ready trong {_READY_TIMEOUT:.0f}s → kill, không fallback Gemini")
                self._kill_dead()
                return False
            try:
                msg = json.loads(line.strip())
            except ValueError:
                continue
            if msg.get("info") or msg.get("warn"):
                logger.info(f"[local-sdxl] {msg}")
                continue
            if msg.get("ready"):
                logger.info("[local-sdxl] worker sẵn sàng")
                return True
            if msg.get("fatal"):
                logger.warning(f"[local-sdxl] worker chết khi load → không fallback Gemini: {msg['fatal']}")
                self._kill_dead()
                return False
        logger.warning("[local-sdxl] quá hạn chờ ready → kill, không fallback Gemini")
        self._kill_dead()
        return False

    def generate(self, *, prompt: str, out_path: str, aspect_ratio=None, input_image_paths=None) -> str | None:
        """Khớp GeminiImageProvider.generate. aspect_ratio bỏ qua; input_image_paths dùng ảnh đầu tiên
        làm ảnh tham khảo nếu có. None → caller báo lỗi rõ."""
        ref = next((p for p in (input_image_paths or []) if p and os.path.exists(p)), "")
        if not ref:
            lib_path = _try_doodle_library(prompt, out_path)
            if lib_path:
                return lib_path
        with self._lock:
            if not self._ensure():
                return None
            try:
                # SEED theo NỘI DUNG (không cố định 42) → mỗi prompt KHÁC ra ảnh KHÁC (sửa lỗi "5 doodle cùng
                # 1 cô gái" do seed cứng + style đè). Cùng prompt vẫn tái lập (deterministic).
                seed_src = f"{prompt}|{ref}"
                seed = int(hashlib.md5(seed_src.encode("utf-8")).hexdigest()[:8], 16) % 2147483647
                payload = {"prompt": prompt, "out_path": out_path, "seed": seed}
                if ref:
                    payload["input_image_path"] = ref
                self._proc.stdin.write(json.dumps(payload) + "\n")
                self._proc.stdin.flush()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[local-sdxl] ghi yêu cầu lỗi → kill: {str(exc)[:140]}")
                self._kill_dead()
                return None
            # chờ kết quả 1 ảnh CÓ HẠN GIỜ — quá hạn = GPU treo → kill + báo lỗi rõ.
            left = _GEN_TIMEOUT
            while left > 0:
                t0 = time.monotonic()
                line = self._next(left)
                left -= time.monotonic() - t0
                if line is None:
                    logger.warning(f"[local-sdxl] gen QUÁ HẠN {_GEN_TIMEOUT:.0f}s (GPU treo?) → kill, không fallback Gemini")
                    self._kill_dead()
                    return None
                try:
                    msg = json.loads(line.strip())
                except ValueError:
                    continue
                if msg.get("info") or msg.get("warn"):
                    continue
                if "ok" in msg:
                    if not (msg.get("ok") and os.path.exists(out_path)):
                        return None
                    issues = _generated_image_issues(out_path, prompt)
                    if issues and "edge_cut" in issues and _pad_generated_image(out_path):
                        issues = _generated_image_issues(out_path, prompt)
                    if issues:
                        logger.warning(f"[local-sdxl] bỏ ảnh local lỗi {issues} → không fallback Gemini: {out_path}")
                        try:
                            os.remove(out_path)
                        except OSError:
                            pass
                        return None
                    return out_path
            logger.warning(f"[local-sdxl] gen quá hạn {_GEN_TIMEOUT:.0f}s → kill, không fallback Gemini")
            self._kill_dead()
            return None

    def shutdown(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=15)
            except Exception:  # noqa: BLE001
                try:
                    self._proc.kill()
                except Exception:  # noqa: BLE001
                    pass
        self._proc = None


class HybridImageProvider:
    """Local trước (rẻ + đồng nhất), hỏng/None → Gemini (bảo hiểm)."""

    def __init__(self):
        self._local = LocalImageProvider()
        self._gemini = None
        self._gemini_credit_exhausted = False

    def generate(self, *, prompt: str, out_path: str, aspect_ratio=None, input_image_paths=None) -> str | None:
        lower_prompt = prompt.lower()
        if input_image_paths and "person in the reference image" in lower_prompt:
            prompt += (
                " IMPORTANT face-only rule: draw ONLY the face and head of the reference person, cropped at the neck; "
                "no shoulders, no jacket, no hands, no arms, no torso, no full body, no small full-body copy of the reference."
            )
            lower_prompt = prompt.lower()

        def _gemini_generate_checked() -> str | None:
            if self._gemini_credit_exhausted:
                return None
            if self._gemini is None:
                from video_engine.image_stage.gemini import GeminiImageProvider
                self._gemini = GeminiImageProvider()
            try:
                p = self._gemini.generate(prompt=prompt, out_path=out_path, aspect_ratio=aspect_ratio,
                                          input_image_paths=input_image_paths)
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                if "RESOURCE_EXHAUSTED" in msg or "prepayment credits are depleted" in msg:
                    self._gemini_credit_exhausted = True
                    logger.warning("[hybrid-image] Gemini hết credit, bỏ qua Gemini trong phiên này")
                    return None
                raise
            if p and "Subject is:" in prompt:
                issues = _generated_image_issues(out_path, prompt)
                if issues:
                    try:
                        os.remove(out_path)
                    except OSError:
                        pass
                    if (
                        "person in the reference image" in lower_prompt
                        and not re.search(r"\b(whole body|entire body|head to toe)\b", lower_prompt)
                        and not ("full body" in lower_prompt and "no full body" not in lower_prompt)
                    ):
                        retry_prompt = (
                            prompt + " Regenerate once more as FACE ONLY: only the face and head, cropped at the neck, "
                            "full hair, ears, chin, and glasses inside the canvas, generous white padding, no shoulders, "
                            "no jacket, no hands, no arms, no torso, no full body, no small body copy."
                        )
                    else:
                        retry_prompt = (
                            prompt + " Regenerate once more with the whole subject fully inside the canvas, generous "
                            "white padding on every side, one single natural hand-drawn subject, no duplicate, not tiny. "
                            "For any face/person, use a head-and-shoulders portrait with full hair, ears, chin, glasses, "
                            "and shoulders inside the frame, not an extreme close-up. Make the outline visibly wobbly "
                            "and hand-drawn, with softer train-like colors, not a clean app icon or sticker."
                        )
                    p = self._gemini.generate(prompt=retry_prompt, out_path=out_path, aspect_ratio=aspect_ratio,
                                              input_image_paths=input_image_paths)
                    retry_issues = _generated_image_issues(out_path, prompt) if p else ["missing"]
                    if retry_issues and set(retry_issues) <= {"edge_cut"} and _pad_generated_image(out_path):
                        retry_issues = _generated_image_issues(out_path, prompt)
                    if not retry_issues:
                        logger.info(f"[hybrid-image] Gemini retry sửa được ảnh lỗi {issues}: {out_path}")
                        return p
                    logger.warning(f"[hybrid-image] bỏ ảnh Gemini lỗi {issues} rồi retry vẫn lỗi {retry_issues}: {out_path}")
                    try:
                        os.remove(out_path)
                    except OSError:
                        pass
                    return None
            return p

        tried_local_ref = False
        if input_image_paths and _PERSON_PROMPT_RE.search(lower_prompt) and not _LOCAL_REF_BLOCK_RE.search(prompt):
            tried_local_ref = True
            local_prompt = _local_subject_prompt(prompt)
            local_refs = _local_reference_paths(prompt, input_image_paths)
            p = self._local.generate(prompt=local_prompt, out_path=out_path, aspect_ratio=aspect_ratio,
                                     input_image_paths=local_refs)
            if p:
                return p

        if input_image_paths:
            try:
                p = _gemini_generate_checked()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[hybrid-image] Gemini style-ref lỗi, thử local dự phòng: {str(exc)[:140]}")
                p = None
            if p:
                return p

        if input_image_paths and _LOCAL_REF_BLOCK_RE.search(prompt):
            return None

        local_prompt = _local_subject_prompt(prompt)
        local_refs = _local_reference_paths(prompt, input_image_paths)
        if not tried_local_ref:
            p = self._local.generate(prompt=local_prompt, out_path=out_path, aspect_ratio=aspect_ratio,
                                     input_image_paths=local_refs)
            if p:
                return p
        try:
            return _gemini_generate_checked()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[hybrid-image] Gemini lỗi, không có ảnh dự phòng: {str(exc)[:140]}")
            return None

    def shutdown(self) -> None:
        self._local.shutdown()
