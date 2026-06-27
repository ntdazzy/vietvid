"""critic.py — cổng tự-review chất lượng kịch bản long_narrative TRƯỚC render (chống "AI slop").

3 cổng + 1 vòng lặp (phỏng director-review của engine product, video_engine/pipeline.py:216-281):
  - review_content : LLM chấm hook/cà-khịa/quan-điểm/retention/CTA/flow (0-10) + weaknesses + rewrite_hints
  - review_facts   : LLM STRICT đối chiếu narration vs NGUỒN TIN (chống bịa) — CHỈ cờ khi MÂU THUẪN RÕ
  - gate_structure : DETERMINISTIC — beat[0]=hook, beat cuối có CTA (like/đăng ký/chia sẻ) + câu hỏi, đủ beat
  - critique_and_improve : vòng review→viết-lại (giữ bản điểm cao nhất), fail-open + cờ critic_failed

Reuse: `_loads_lenient` (video_engine/director/critic.py) + `complete_with_fallback`. KHÔNG đụng critic
engine product. Mọi LLM call FAIL-OPEN (lỗi → coi như đạt, gắn cờ) để critic không bao giờ chặn pipeline.
"""

from __future__ import annotations

import re

from config.settings import settings
from core.logger import logger
from video_engine.director.critic import _loads_lenient  # parser JSON bền (string-aware)

# ── Structural keyword sets (deterministic gate) ─────────────────────────
_CTA_KW = ("like", "đăng ký", "đăng kí", "subscribe", "chia sẻ", "share", "kênh")
_ENGAGE_KW = ("tranh luận", "comment", "bình luận", "bạn nghĩ", "ý kiến", "?")
_DRY_OPEN = ("hôm nay", "hôm qua", "vừa qua", "mới đây có tin", "tin tức hôm", "gần đây có")
# Gọi người xem ẤM ('chúng ta/anh em/các bạn') GIỜ LÀ CHẤT KÊNH (Vui Vẻ/Lóng dùng hàng chục lần/video) —
# KHÔNG còn coi là thảo mai. Chỉ guard biến thể NŨNG NỊU nịnh; các '...ơi' đã bị AI_FILLER cấm cứng.
_VIEWER_ADDR_RE = re.compile(r"\b(đúng không nào|đúng không bạn)\b", re.IGNORECASE)
# Từ đệm "AI-ese" + tic NŨNG NỊU. NGUỒN DUY NHẤT — director._rubric import lại để cấm song song (DRY).
# scrub_ai_filler XOÁ THẲNG các cụm này khỏi cả TTS lẫn caption → ĐỪNG để cụm đời-thật của kênh vào đây
# (vd "thú thật là", "anh em cứ tưởng tượng", "chúng ta" — corpus 2 kênh DÙNG, bỏ vào là tự cắt giọng kênh).
AI_FILLER = (
    "có thể nói rằng", "vậy đó", "tóm lại là",
    "thú vị thay", "đáng chú ý là", "không thể phủ nhận", "trên thực tế là",
    # tic NŨNG NỊU / kéo âm — corpus 2 kênh KHÔNG có; nhồi vào nghe "thảo mai".
    "mấy ông ơi", "các bạn ơi", "anh em ơi", "bạn ơi", "đúng không bạn", "đúng không nào",
    "nha bạn", "nè bạn",
)
_FILLER_RE = [re.compile(rf"\s*{re.escape(w)}\s*,?", re.IGNORECASE) for w in AI_FILLER]

# Tic "đó" cuối câu ("...thôi đó.", "...vậy đó.") lặp nghe máy/giượng. Bỏ khi nó đứng CUỐI câu,
# NHƯNG GIỮ khi là cụm xác định có nghĩa ("nào đó", "gì đó", "ai đó", "chỗ đó", "lúc đó"...).
_DO_PROTECT = {
    "nào", "gì", "ai", "đâu", "kia", "này", "nọ", "chỗ", "lúc", "khi", "hôm", "nơi",
    "người", "cái", "con", "thằng", "ông", "bà", "cô", "anh", "chị", "đứa", "bé",
}
_DO_TIC_RE = re.compile(r"(\S+)\s+đó(\s*[.!?…]|\s*$)", re.IGNORECASE)
# particle lặp "đó đó", "nè nè", "đấy đấy" → còn 1
_DBL_PARTICLE_RE = re.compile(r"\b(đó|nè|đấy)\b(?:\s+\1\b)+", re.IGNORECASE)
# "nè"/"đấy" cuối câu = tic thuần (không có nghĩa xác định như "nào đó") → bỏ thẳng
_NE_TAIL_RE = re.compile(r"\s+(?:nè|đấy)(?=\s*[.!?…]|\s*$)", re.IGNORECASE)


def _strip_tail_particles(text: str) -> str:
    """Bỏ tic cuối câu lặp: 'đó đó'/'nè nè' → 1; bỏ 'nè'/'đấy' cuối câu; bỏ 'đó' cuối câu
    (GIỮ 'nào đó/gì đó/chỗ đó'...). 'đó' lẻ giữa câu vẫn giữ — chỉ trị tic CUỐI câu."""
    out = _DBL_PARTICLE_RE.sub(r"\1", text or "")   # đó đó → đó
    out = _NE_TAIL_RE.sub("", out)                  # bỏ nè/đấy cuối câu

    def _repl(m: "re.Match[str]") -> str:
        prev = m.group(1).lower().strip(",;:\"'")
        if prev in _DO_PROTECT:
            return m.group(0)             # giữ "nào đó.", "chỗ đó."
        return m.group(1) + m.group(2)    # bỏ tic: "thôi đó." → "thôi."
    return _DO_TIC_RE.sub(_repl, out)


def scrub_ai_filler(text: str) -> str:
    """Lưới chốt DETERMINISTIC: bỏ sạch cụm AI-ese còn sót sau critic loop (LLM cứng đầu giữ
    'vậy đó'...) + bỏ tic 'đó' cuối câu. Gộp space, dọn dấu câu, viết hoa đầu câu.
    Text này dùng cho CẢ TTS lẫn caption nên phải sạch một lần là xong."""
    out = text or ""
    for rx in _FILLER_RE:
        out = rx.sub(" ", out)
    out = _strip_tail_particles(out)
    out = re.sub(r"\s+", " ", out)
    out = re.sub(r"\s+([.,!?…])", r"\1", out)
    out = re.sub(r",\s*([.!?…])", r"\1", out)   # 'toang,.' → 'toang.' (bỏ phẩy thừa trước dấu kết)
    out = re.sub(r",\s*,", ",", out)            # gộp phẩy đôi
    out = out.strip(" ,").strip()
    return (out[:1].upper() + out[1:]) if out else out

# ── Content critic ───────────────────────────────────────────────────────
_CONTENT_SYSTEM = (
    "Bạn là critic kịch bản kênh YouTube 'điểm tin - giải trí' Việt (phong cách Lóng / Đức Reaction "
    "/ Thanh Pahm). Chấm thẳng tay, chỉ trả JSON."
)
_CONTENT_RUBRIC = """Chấm KỊCH BẢN (các beat) dưới đây cho video cà khịa giải trí. Thang 0-2 mỗi chiều:
- hook (0-2): beat ĐẦU có gây sốc/tò mò trong ~5s không (KHÔNG mở khô khan 'hôm nay có tin...')?
- cakhia (0-2): mật độ HÀI / CÀ KHỊA / nói lái / ví von đời thường — đúng chất Lóng/Đức/Thanh Pahm?
- original_opinion (0-2): có QUAN ĐIỂM GỐC / bình luận riêng, KHÔNG đọc tin trơn (lá chắn 'inauthentic')?
- retention (0-2): nhịp GIỮ CHÂN, mở vòng tò mò, không lê thê / lặp khuôn?
- cta (0-2): beat CUỐI kêu gọi like / đăng ký / chia sẻ + câu hỏi tranh luận?
- flow (0-2): biến thiên cấu trúc, lời đời thường, không liệt kê khô?
score = tổng 6 chiều quy về thang 0-10 (vd 6 chiều đều 1.5 → ~7.5).
TRẢ DUY NHẤT JSON:
{"hook":0-2,"cakhia":0-2,"original_opinion":0-2,"retention":0-2,"cta":0-2,"flow":0-2,"score":0-10,
 "weaknesses":["điểm yếu CỤ THỂ, ngắn"],"rewrite_hints":["gợi ý SỬA cụ thể cho biên kịch (beat nào, sửa gì)"]}

CHỦ ĐỀ: %(topic)s
KỊCH BẢN ([i] label | callout | lời kể):
%(script)s"""

# ── Fact critic (anti-bịa) ───────────────────────────────────────────────
_FACT_SYSTEM = "Bạn là người kiểm chứng dữ kiện NGHIÊM KHẮC nhưng công bằng. Chỉ trả JSON."
_FACT_RUBRIC = """Đối chiếu LỜI KỂ với NGUỒN TIN. Tìm số liệu / tên riêng / sự kiện trong LỜI KỂ **MÂU THUẪN RÕ** với NGUỒN.
QUY TẮC NGHIÊM:
- CHỈ gắn cờ mismatch khi MÂU THUẪN / SAI RÕ so với nguồn (vd nguồn 3-0, lời kể nói 2-1).
- BỎ QUA nếu chỉ THIẾU trong nguồn — suy luận / bình luận / cà khịa chung KHÔNG phải bịa.
- KHÔNG bắt lỗi quan điểm, giọng điệu, ví von.
TRẢ DUY NHẤT JSON:
{"fact_ok": true/false, "mismatches":[{"claim":"câu/số SAI trong lời kể","why":"nguồn nói khác thế nào"}],
 "unverified":["số/tên không có trong nguồn (chỉ cảnh báo nhẹ, KHÔNG chặn)"]}

NGUỒN TIN:
%(source)s

LỜI KỂ:
%(narration)s"""


def _script_for_prompt(script) -> str:
    # KHÔNG cắt giữa kịch bản: critic phải thấy ĐỦ beat (nhất là beat CUỐI = CTA), nếu không sẽ chấm
    # cta=0 oan. 20K ký tự dư cho ~21 beat (Gemini 1M / Groq 128K token thoải mái). Nếu vượt → giữ
    # đầu + 3 beat cuối (CTA luôn nằm trong tầm critic).
    lines = [f"[{i}] {b.label} | {b.callout} | {b.narration_text}" for i, b in enumerate(script.beats)]
    blob = "\n".join(lines)
    if len(blob) <= 20000:
        return blob
    head = "\n".join(lines[:-3])[:16000]
    tail = "\n".join(lines[-3:])
    return head + "\n…(rút gọn giữa)…\n" + tail


def review_content(script, topic: str) -> dict:
    """Chấm chất lượng nội dung (0-10) + rewrite_hints. LLM lỗi → {"score": None} (fail-open)."""
    try:
        from module2_brain.llm.v5_clients import complete_with_fallback

        prompt = _CONTENT_RUBRIC % {"topic": topic or "(không rõ)", "script": _script_for_prompt(script)}
        raw = complete_with_fallback(_CONTENT_SYSTEM, prompt, gemini_model=settings.gemini_model)
        data = _loads_lenient(raw or "")
        if not isinstance(data, dict) or not isinstance(data.get("score"), (int, float)):
            raise ValueError(f"content critic thiếu score: {(raw or '')[:120]}")
        data["score"] = max(0.0, min(10.0, float(data["score"])))
        data["weaknesses"] = [str(w) for w in (data.get("weaknesses") or [])][:6]
        data["rewrite_hints"] = [str(h) for h in (data.get("rewrite_hints") or [])][:6]
        return data
    except Exception as exc:  # noqa: BLE001 — fail-open: critic không được nghẽn pipeline
        logger.warning(f"[lf-critic] content fail-open: {str(exc)[:200]}")
        return {"score": None, "weaknesses": [], "rewrite_hints": []}


def review_facts(script, source_text: str) -> dict:
    """Đối chiếu narration vs nguồn (chống bịa). Nguồn rỗng → bỏ qua. LLM lỗi → fail-open (coi đạt)."""
    src = (source_text or "").strip()
    if not src:
        return {"fact_ok": True, "skipped": True, "mismatches": [], "unverified": []}
    try:
        from module2_brain.llm.v5_clients import complete_with_fallback

        prompt = _FACT_RUBRIC % {"source": src[:6000], "narration": script.full_narration[:6000]}
        raw = complete_with_fallback(_FACT_SYSTEM, prompt, gemini_model=settings.gemini_model)
        data = _loads_lenient(raw or "")
        if not isinstance(data, dict):
            raise ValueError("fact critic không phải dict")
        mism = [m for m in (data.get("mismatches") or []) if isinstance(m, dict)][:8]
        return {
            "fact_ok": bool(data.get("fact_ok", not mism)) and not mism,
            "skipped": False,
            "mismatches": mism,
            "unverified": [str(u) for u in (data.get("unverified") or [])][:8],
        }
    except Exception as exc:  # noqa: BLE001 — fail-open
        logger.warning(f"[lf-critic] fact fail-open: {str(exc)[:200]}")
        return {"fact_ok": True, "skipped": True, "mismatches": [], "unverified": [], "error": str(exc)[:150]}


def gate_structure(script, *, min_beats: int = 5) -> dict:
    """DETERMINISTIC: beat[0]=hook, beat cuối có CTA (like/đăng ký/chia sẻ) + câu hỏi, đủ beat."""
    beats = script.beats
    if not beats:
        return {"hook_ok": False, "cta_ok": False, "nbeats_ok": False, "failures": ["kịch bản rỗng"]}
    first = beats[0]
    first_txt = (first.narration_text or "").lower()
    dry = any(first_txt.startswith(d) for d in _DRY_OPEN)
    # Hook DETERMINISTIC = chỉ bắt mở KHÔ (mẫu dở RÕ: "hôm nay/hôm qua có tin..."). CHẤT LƯỢNG hook
    # do CHIỀU 'hook' của LLM critic gác (sàn trong `passed`). Cố ý KHÔNG đòi "phải có số / có '?'":
    # hook hay không nhất thiết có số (mở bằng tuyên bố sốc/cà khịa cũng là hook); đòi số sẽ LOẠI OAN
    # hook tốt. '?' bị bỏ vì rubric CẤM câu hỏi suông. Mở kiểu "Mấy ông ơi..." là SAI (gọi người xem).
    hook_ok = not dry

    last = beats[-1]
    last_blob = (last.label + " " + last.callout + " " + last.narration_text).lower()
    has_cta = any(k in last_blob for k in _CTA_KW)
    has_engage = any(k in last_blob for k in _ENGAGE_KW)
    cta_ok = has_cta and has_engage
    nbeats_ok = len(beats) >= min_beats

    full_txt = " ".join((b.narration_text or "") for b in beats).lower()
    fillers = sorted({w for w in AI_FILLER if w in full_txt})
    # CHỈ chặn khi spam cụm NŨNG NỊU nịnh ('đúng không nào/bạn') > 3 lần. 'chúng ta/anh em/các bạn' KHÔNG
    # còn bị tính — đó là xưng-hô đồng bọn đặc trưng Vui Vẻ/Lóng, cấm là giết chất giọng. ('...ơi' cấm cứng.)
    addr_n = len(_VIEWER_ADDR_RE.findall(full_txt))
    addr_dense = addr_n > 3

    failures: list[str] = []
    if not hook_ok:
        failures.append("Beat ĐẦU chưa phải hook gây tò mò (đừng mở 'hôm nay/hôm qua có tin...').")
    if not has_cta:
        failures.append("Beat CUỐI thiếu CTA: thêm kêu gọi like / đăng ký / CHIA SẺ kênh.")
    if not has_engage:
        failures.append("Beat CUỐI thiếu câu hỏi tranh luận để kích comment.")
    if not nbeats_ok:
        failures.append(f"Quá ít beat ({len(beats)} < {min_beats}).")
    if fillers:
        failures.append("Có từ đệm máy móc kiểu AI (" + ", ".join(fillers) + ") — bỏ hết, viết lại cho đời.")
    if addr_dense:
        failures.append(f"Spam nũng nịu nịnh ({addr_n} lần 'đúng không nào/bạn') — bỏ, kể tự nhiên đi.")
    return {"hook_ok": hook_ok, "cta_ok": cta_ok, "nbeats_ok": nbeats_ok, "ai_filler": fillers,
            "addr_dense": addr_dense, "failures": failures}


def critique_and_improve(script, topic: str, source_text: str = "", *, regenerate=None):
    """Vòng review→viết-lại long_narrative (phỏng pipeline.py:216-281). Trả (best_script, verdict).

    `regenerate(hints: list[str]) -> LongformScript | None`: gọi lại Director với gợi ý sửa. None →
    không lặp (chỉ chấm 1 lần). FAIL-OPEN: critic LLM lỗi → score=None coi như đạt + cờ critic_failed.
    """
    min_beats = int(settings.longform_min_beats or 5)
    if not settings.longform_critic_enabled:
        struct = gate_structure(script, min_beats=min_beats)  # vẫn báo cấu trúc dù tắt loop
        return script, {"enabled": False, "rounds": 0, "structural_failures": struct["failures"]}

    rounds = max(1, int(settings.longform_critic_max_rounds or 1))
    min_score = float(settings.longform_critic_min_score or 7.0)
    min_cakhia = float(settings.longform_critic_min_cakhia or 0.0)
    fact_on = settings.longform_fact_critic_enabled
    strict = settings.longform_fact_critic_strict

    best, best_verdict, best_key, critic_failed = script, None, (-1, -1.0), False
    attempt = 0
    while attempt < rounds:
        attempt += 1
        struct = gate_structure(script, min_beats=min_beats)
        fact = review_facts(script, source_text) if fact_on else {"fact_ok": True, "skipped": True, "mismatches": [], "unverified": []}
        content = review_content(script, topic)
        score = content.get("score")
        if score is None:
            critic_failed = True
        eff_score = float(score) if isinstance(score, (int, float)) else min_score  # fail-open
        verdict = {
            "enabled": True, "round": attempt, "score": score,
            "dims": {k: content.get(k) for k in ("hook", "cakhia", "original_opinion", "retention", "cta", "flow")},
            "fact_ok": fact.get("fact_ok", True), "fact_skipped": fact.get("skipped", False),
            "fact_mismatches": fact.get("mismatches", []), "fact_unverified": fact.get("unverified", []),
            "structural_failures": struct["failures"], "weaknesses": content.get("weaknesses", []),
            "critic_failed": critic_failed,
        }
        # SÀN RIÊNG chiều cà-khịa + hook (0-2): chống lọt kịch bản điểm-TỔNG cao nhưng NHẠT (cakhia/hook
        # thấp mà các chiều khác kéo trung bình lên). Chỉ áp khi LLM chấm được (None = fail-open → bỏ qua).
        def _dim_below(name: str) -> bool:
            v = verdict["dims"].get(name)
            return isinstance(v, (int, float)) and float(v) < min_cakhia
        cakhia_low, hook_low = _dim_below("cakhia"), _dim_below("hook")
        # filler kiểu AI nằm TRONG điều kiện passed → còn filler thì KHÔNG đạt → ép viết lại (bounded
        # bởi max_rounds; hết vòng vẫn dơ thì fail-open giữ bản điểm cao nhất). Vá lỗ hổng "filler mềm".
        passed = (
            eff_score >= min_score and verdict["fact_ok"]
            and struct["hook_ok"] and struct["cta_ok"] and not struct.get("ai_filler")
            and not struct.get("addr_dense") and not cakhia_low and not hook_low
        )
        verdict["passed"] = passed
        # Best = ưu tiên bản ĐẠT (passed) rồi mới tới điểm — tránh vứt bản ĐÃ SỬA fact/cấu trúc chỉ vì
        # điểm bằng (lỗi cũ: giữ bản fail → strict mode FAIL oan dù vòng sau đã sinh bản sạch).
        key = (1 if passed else 0, eff_score)
        if key > best_key:
            best_key, best, best_verdict = key, script, verdict
        logger.info(
            f"[lf-critic] vòng {attempt}/{rounds}: score={score} fact_ok={verdict['fact_ok']} "
            f"struct={'ok' if not struct['failures'] else struct['failures']}"
        )
        if passed or attempt >= rounds or regenerate is None:
            break
        hints = (
            list(content.get("rewrite_hints") or [])
            + struct["failures"]
            + [f"SAI FACT: {m.get('claim', '')} → {m.get('why', '')}" for m in fact.get("mismatches", [])]
        )
        if cakhia_low:
            hints.append("Kịch bản CHƯA ĐỦ CÀ KHỊA/hài — thêm nói lái, ví von đời thường, tự cà khịa mình "
                         "trước, bình luận bựa; ĐỪNG đọc tin trơn.")
        if hook_low:
            hints.append("HOOK beat đầu YẾU — mở bằng câu sốc/tò mò/số liệu gây 'ngừng lướt' trong 3 giây đầu.")
        try:
            new_script = regenerate(hints)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[lf-critic] regenerate lỗi → giữ bản tốt nhất: {str(exc)[:150]}")
            break
        if not new_script or not getattr(new_script, "beats", None):
            break
        script = new_script

    # Lưới chốt: LLM đôi khi giữ filler (vd 'vậy đó') qua cả vòng rewrite → bỏ deterministic trên
    # bản BEST trước khi trả (sửa tại text dùng cho cả TTS + caption).
    scrubbed = 0
    for b in best.beats:
        for blk in b.narration_blocks:
            new = scrub_ai_filler(blk.text)
            if new != blk.text:
                blk.text = new
                scrubbed += 1
    best_verdict = best_verdict or {"enabled": True, "round": attempt}
    best_verdict["rounds"] = attempt
    best_verdict["ai_filler_scrubbed"] = scrubbed
    # strict: bịa RÕ (không skip) → cờ để runner FAIL job
    best_verdict["fact_fail_hard"] = bool(
        strict and not best_verdict.get("fact_ok", True) and not best_verdict.get("fact_skipped")
    )
    return best, best_verdict
