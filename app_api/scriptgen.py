"""Bộ máy sinh kịch bản quảng cáo Việt (công nghệ lõi, chạy KHÔNG cần key).

Cho người dùng XEM TRƯỚC + SỬA kịch bản trước khi đốt credit render (giống Arcads/autovis).
Lõi là bộ template theo GÓC thuyết phục (giống ANGLES của Strategist) — sinh ngay, miễn phí,
tiếng Việt đời thường. Khi có key Gemini/Groq, ``apply_strategist`` phủ brief thông minh lên
(hook/angle/beats sắc hơn) theo kiểu fail-soft: lỗi key → vẫn còn bản template dùng được.

Pure-Python, không I/O, không mạng → test bằng vận hành thật, không mock.
"""

from __future__ import annotations

# Góc thuyết phục — khớp ANGLES của video_engine/director/strategist.py.
ANGLE_LABELS = {
    "problem_solution": "Vấn đề → Giải pháp",
    "social_proof": "Đám đông tin dùng",
    "transformation": "Lột xác trước → sau",
    "fomo_scarcity": "Sợ bỏ lỡ / sắp hết",
    "comparison": "So sánh hơn hẳn",
    "curiosity_gap": "Tò mò khó cưỡng",
}

# Mỗi góc: hook (0-2s) + 5 beat theo thứ tự ưu tiên (hook…cta). nbeats sẽ chọn tập con.
# Lời thoại đời thường, ngôi thứ nhất (UGC tự quay), chèn {name}/{price}/{category}.
_ANGLES: dict[str, dict] = {
    "problem_solution": {
        "hook": "{name} — giải pháp gọn cho vụ {category} luôn nè!",
        "beats": [
            ("hook", "{hook}", "Cầm {name} giơ khoe trước camera, mặt hào hứng"),
            ("pain", "Trước mình vật vã với vụ {category} miết, bực dễ sợ.", "Cảnh tái hiện lúc loay hoay, khó chịu"),
            ("benefit", "Từ ngày có {name} là nhẹ hẳn, tiện gấp mấy lần.", "Dùng thử {name}, mọi thứ trơn tru"),
            ("desire", "Dùng vô thấy đáng tiền, ai mượn cũng đòi mua theo.", "Khoe kết quả, gật gù ưng ý"),
            ("cta", "Giá {price} thôi, để sẵn giỏ hàng rồi, bấm vô lẹ nha!", "Chỉ tay về phía giỏ hàng, cười"),
        ],
    },
    "social_proof": {
        "hook": "Cả nhà rủ nhau mua {name}, mình cũng phải thử!",
        "beats": [
            ("hook", "{hook}", "Cầm {name}, vẻ tò mò 'sao ai cũng mua'"),
            ("pain", "Lướt đâu cũng thấy người ta khen {category} này.", "Cảnh review của nhiều người (gợi ý)"),
            ("benefit", "Mua về xài thử mới hiểu vì sao nó hot tới vậy.", "Dùng {name}, gật đầu công nhận"),
            ("desire", "Giờ tới lượt mình nghiện, đúng kiểu mua là không hối.", "Ôm sản phẩm khoái chí"),
            ("cta", "Còn chần chừ gì, {price} thôi, chốt cùng hội luôn nè!", "Vẫy tay rủ, chỉ giỏ hàng"),
        ],
    },
    "transformation": {
        "hook": "Trước với sau khi có {name} — khác một trời một vực!",
        "beats": [
            ("hook", "{hook}", "Split before/after, biểu cảm 'wow'"),
            ("pain", "Hồi trước nhìn chán lắm, tự ti dễ sợ.", "Cảnh 'trước' hơi xìu"),
            ("benefit", "Có {name} vô phát là lên đời, tự tin hẳn ra.", "Cảnh 'sau' rạng rỡ, xoay khoe"),
            ("desire", "Soi gương mà mê, ra đường ai cũng hỏi mua ở đâu.", "Tự ngắm, cười tươi"),
            ("cta", "Muốn lột xác như mình thì {price}, bấm giỏ hàng nha!", "Chỉ giỏ hàng, nháy mắt"),
        ],
    },
    "fomo_scarcity": {
        "hook": "{name} sắp hết hàng rồi, nhanh tay kẻo tiếc!",
        "beats": [
            ("hook", "{hook}", "Cầm {name}, vẻ gấp gáp 'lẹ lên'"),
            ("benefit", "Đợt này deal hời lắm, qua đợt là về giá gốc liền.", "Khoe {name} + nhấn 'giá tốt'"),
            ("desire", "Mình canh mãi mới hốt được, sướng gì đâu.", "Ôm sản phẩm, vui ra mặt"),
            ("pain", "Bạn mình chần chừ cái hết sạch, tiếc hùi hụi.", "Cảnh tiếc nuối (gợi ý)"),
            ("cta", "Chỉ {price} thôi, còn hàng là còn cơ hội, chốt liền!", "Chỉ giỏ hàng, ra hiệu nhanh"),
        ],
    },
    "comparison": {
        "hook": "Thử {name} xong là khỏi quay lại loại cũ luôn!",
        "beats": [
            ("hook", "{hook}", "Đặt {name} cạnh loại cũ, so sánh"),
            ("pain", "Loại rẻ tiền dùng bực mình, mau hư thấy ghê.", "Cảnh loại cũ trục trặc"),
            ("benefit", "{name} thì khác hẳn — mượt, bền, đáng từng đồng.", "Dùng {name} trơn tru"),
            ("desire", "Một lần đầu tư xài đã, khỏi mua tới mua lui.", "Gật gù hài lòng"),
            ("cta", "Có {price} mà nâng cấp hẳn, bấm giỏ hàng đi nha!", "Chỉ giỏ hàng dứt khoát"),
        ],
    },
    "curiosity_gap": {
        "hook": "Cái {name} này làm được điều bạn không ngờ tới đâu!",
        "beats": [
            ("hook", "{hook}", "Giấu một phần {name}, vẻ bí ẩn"),
            ("benefit", "Nhìn vậy thôi chứ công dụng bất ngờ cực kỳ.", "Hé lộ {name} hoạt động"),
            ("desire", "Coi xong là hiểu vì sao mình mê tít luôn á.", "Biểu cảm thích thú"),
            ("pain", "Biết sớm thì đỡ phí tiền mấy món vô dụng trước.", "Lắc đầu nuối tiếc nhẹ"),
            ("cta", "Tò mò thì thử đi, {price} thôi, link giỏ hàng nha!", "Chỉ giỏ hàng, cười bí mật"),
        ],
    },
}

# Chọn beat theo số lượng — luôn giữ hook (đầu) + cta (cuối).
_PICK = {3: (0, 2, 4), 4: (0, 1, 2, 4), 5: (0, 1, 2, 3, 4)}

# Nhịp đọc tiếng Việt quảng cáo ~2.5 từ/giây.
_WORDS_PER_SEC = 2.5


def _fill(s: str, ctx: dict[str, str]) -> str:
    out = s
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", v)
    return out


def generate_script(
    *,
    product: dict,
    angle: str = "problem_solution",
    seconds: int = 15,
    voice_gender: str = "female",
) -> dict:
    """Sinh kịch bản quảng cáo Việt có cấu trúc (hook + beats + cta + captions).

    Thuần template (miễn phí, tức thì). Trả dict sẵn sàng cho frontend xem/sửa rồi render.
    """
    if angle not in _ANGLES:
        angle = "problem_solution"
    seconds = max(6, min(60, int(seconds)))
    spec = _ANGLES[angle]

    name = (product.get("name") or "sản phẩm này").strip()
    category = (product.get("category") or "này").strip()
    price = (product.get("price") or "").strip() or "giá tốt lắm"
    ctx = {"name": name, "category": category, "price": price}
    ctx["hook"] = _fill(spec["hook"], ctx)

    nbeats = max(3, min(5, round(seconds / 3)))
    picks = _PICK[nbeats]
    raw = [spec["beats"][i] for i in picks]

    # Chia thời lượng đều theo beat (làm tròn, beat cuối nuốt phần dư).
    step = seconds / nbeats
    beats = []
    captions = []
    for idx, (label, line, scene) in enumerate(raw):
        narration = _fill(line, ctx)
        t_start = round(idx * step, 1)
        t_end = seconds if idx == nbeats - 1 else round((idx + 1) * step, 1)
        beats.append({
            "label": label,
            "t_start": t_start,
            "t_end": t_end,
            "narration": narration,
            "scene": _fill(scene, ctx),
        })
        captions.append(narration)

    full = " ".join(captions)
    return {
        "angle": angle,
        "angle_label": ANGLE_LABELS[angle],
        "duration_seconds": seconds,
        "voice_gender": voice_gender if voice_gender in ("female", "male") else "female",
        "hook_line": ctx["hook"],
        "beats": beats,
        "cta": beats[-1]["narration"],
        "captions": captions,
        "narration_full": full,
        "word_count": len(full.split()),
        "target_words": round(seconds * _WORDS_PER_SEC),
        "source": "template",
    }


# ── Phụ đề frame-perfect (moat): timing suy từ KỊCH BẢN đã biết, KHÔNG ASR ──────
# Vì mình tự sinh narration → biết chính xác câu nào đọc ở beat nào → cue khít khung,
# 0 lỗi nhận dạng (đối thủ phải ASR lại video → sai chính tả/timing tiếng Việt).
_MAX_CUE_WORDS = 8  # mỗi dòng phụ đề tối đa ~8 từ cho dễ đọc trên màn dọc


def _split_cue_text(text: str, max_words: int = _MAX_CUE_WORDS) -> list[str]:
    """Tách 1 câu narration thành các dòng phụ đề ngắn (ưu tiên cắt ở dấu câu)."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    cur: list[str] = []
    for w in words:
        cur.append(w)
        ends_clause = w.endswith((",", ".", "!", "?", "…", ";", ":"))
        if len(cur) >= max_words or (ends_clause and len(cur) >= 4):
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def build_captions(script: dict) -> list[dict]:
    """Trả list cue {index, start, end, text} phủ kín thời lượng, timing đơn điệu tăng.

    Mỗi beat có [t_start, t_end]; chia cửa sổ đó cho các dòng phụ đề theo TỶ LỆ SỐ TỪ
    → dòng dài hiện lâu hơn, khít với nhịp đọc TTS thật."""
    cues: list[dict] = []
    idx = 1
    for beat in script.get("beats") or []:
        t0 = float(beat.get("t_start", 0))
        t1 = float(beat.get("t_end", t0))
        span = max(0.1, t1 - t0)
        lines = _split_cue_text(str(beat.get("narration") or ""))
        if not lines:
            continue
        total_words = sum(len(ln.split()) for ln in lines) or 1
        cursor = t0
        for j, ln in enumerate(lines):
            w = len(ln.split())
            dur = span * (w / total_words)
            start = cursor
            end = t1 if j == len(lines) - 1 else round(cursor + dur, 2)
            cues.append({"index": idx, "start": round(start, 2), "end": end, "text": ln})
            cursor = end
            idx += 1
    return cues


def _ts(sec: float, sep: str) -> str:
    """giây → HH:MM:SS{sep}mmm (sep=',' cho SRT, '.' cho VTT)."""
    if sec < 0:
        sec = 0.0
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_srt(cues: list[dict]) -> str:
    blocks = [
        f"{c['index']}\n{_ts(c['start'], ',')} --> {_ts(c['end'], ',')}\n{c['text']}"
        for c in cues
    ]
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def to_vtt(cues: list[dict]) -> str:
    body = "\n\n".join(
        f"{_ts(c['start'], '.')} --> {_ts(c['end'], '.')}\n{c['text']}" for c in cues
    )
    return "WEBVTT\n\n" + body + ("\n" if body else "")


def apply_strategist(script: dict, brief: dict) -> dict:
    """Phủ CreativeBrief (Strategist, có key) lên bản template → sắc hơn, vẫn fail-soft.

    Chỉ ghi đè các trường brief có thật; thiếu trường nào giữ nguyên bản template.
    """
    if not isinstance(brief, dict):
        return script
    out = dict(script)
    if brief.get("hook_line"):
        out["hook_line"] = str(brief["hook_line"]).strip()
    if brief.get("angle") in ANGLE_LABELS:
        out["angle"] = brief["angle"]
        out["angle_label"] = ANGLE_LABELS[brief["angle"]]
    b_beats = [b for b in (brief.get("beats") or []) if isinstance(b, dict) and b.get("says")]
    if b_beats:
        seconds = out["duration_seconds"]
        n = len(b_beats)
        step = seconds / n
        beats = []
        captions = []
        for idx, b in enumerate(b_beats):
            says = str(b.get("says") or "").strip()
            t_start = round(idx * step, 1)
            t_end = seconds if idx == n - 1 else round((idx + 1) * step, 1)
            beats.append({
                "label": str(b.get("label") or "beat"),
                "t_start": t_start,
                "t_end": t_end,
                "narration": says,
                "scene": str(b.get("shows") or "").strip(),
            })
            captions.append(says)
        out["beats"] = beats
        out["captions"] = captions
        out["narration_full"] = " ".join(captions)
        out["word_count"] = len(out["narration_full"].split())
        out["cta"] = captions[-1] if captions else out.get("cta", "")
    if brief.get("cta_plan"):
        out["cta"] = str(brief["cta_plan"]).strip()
    out["source"] = "strategist+template"
    return out
