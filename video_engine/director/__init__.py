"""Director — Gemini viết storyboard + narration + prompt ảnh/video cho 1 job.

Tái dùng ``complete_with_fallback`` (Gemini → Groq) của module2_brain. Narration bị
kiểm cấm chỉ-đạo-cảnh NGAY tại đây (rẻ hơn nhiều so với phát hiện ở QA audio cuối).
"""

from __future__ import annotations

import json
import re

from config.settings import settings
from core.logger import logger
from video_engine.providers.base import VideoEngineError

# Narration KHÔNG được chứa chỉ đạo cảnh/markup — sẽ bị TTS đọc thành tiếng.
_BANNED_NARRATION = re.compile(
    r"[\[\]{}*#_<>]|\b(cảnh quay|góc máy|camera|zoom|cắt cảnh|prompt|storyboard|shot)\b",
    re.IGNORECASE,
)

# Luật bắt buộc cho `video_prompt` — học từ payload THẬT của autovis (b.shortspin.ai):
# người được MÔ TẢ BẰNG TEXT (KHÔNG gửi ảnh mặt vào model video → né kiểm duyệt deepfake),
# reference chỉ là 1 ảnh SẢN PHẨM. video_prompt theo đúng 3 khối + lời thoại nhúng.
# V8.3-Q1: Seedance bị CẤM vẽ chữ hoàn toàn — chữ giá/hook/CTA vẽ LOCAL (compose/overlays.py)
# từ khóa JSON "text_overlays"; overlay_policy quyết định bắt buộc/tùy chọn/cấm danh sách đó.
_VIDEO_PROMPT_RULES = """
QUY TẮC BẮT BUỘC cho "video_prompt" (tiếng Anh, 1 đoạn liền mạch, ~250-400 từ, học từ autovis):
- KHỐI 1 — Style/format: tỷ lệ {aspect}. ƯU TIÊN kiểu quay UGC TỰ QUAY bằng ĐIỆN THOẠI — chân
  thật, đời thường, hơi mộc (handheld nhẹ, ánh sáng tự nhiên trong nhà/ngoài phố), như clip người
  dùng tự quay. TRÁNH cinematic/studio/TVC bóng bẩy + ánh sáng hoàn hảo (dễ lộ "giả/AI"). "authentic
  amateur UGC phone video, natural imperfect lighting, real Vietnamese girl, candid, not polished,
  real skin tones, no filters".{voice_line}
- KHỐI 2 — Setting + MÔ TẢ SẢN PHẨM SIÊU CHI TIẾT: bối cảnh + tả sản phẩm cực kỹ
  (brand, CHỮ IN trên bao bì/sản phẩm, màu, chất liệu, texture, chi tiết nhận diện) — đây là
  cách giữ logo/nhãn không bị "trôi" ở 480p. Nếu có mô tả sản phẩm cung cấp sẵn thì DÙNG NGUYÊN.
- KHỐI 3 — Hành động theo timecode (0-3s / 3-6s / …) PHẢI KHỚP NARRATION: mỗi mốc minh hoạ ĐÚNG
  ý câu narration đang đọc lúc đó (clip "kể" đúng cái miệng đang nói). VD narration khoe "mới săn
  được" → cảnh cầm/giơ khoe SP hào hứng; "mặc lên tôn dáng" → mặc vào xoay khoe dáng / đi thẳng tới
  camera tự tin cười; "để ở giỏ hàng bấm vô coi" → chỉ tay/ra hiệu về phía giỏ hàng. Mạch hành động
  bám SÁT mạch narration từ đầu tới cuối.{dialogue_rule} CHO PHÉP hiệu ứng dựng trong mô tả:
  transition, speed-ramp, match-cut, SFX cue (vd "whoosh transition at 3s") — Seedance render trọn gói.
- NẾU có nhân vật (KOL): MÔ TẢ NGƯỜI BẰNG TEXT trong video_prompt (tuổi, sắc tộc, tóc, da, vóc dáng,
  trang phục — lấy từ character_sheet). TUYỆT ĐỐI KHÔNG giả định có ảnh mặt người đầu vào;
  người do model TỰ SINH từ mô tả. Khung hình đầu vào chỉ là ẢNH SẢN PHẨM.
- NHÂN VẬT MẶC ĐỊNH (khi KHÔNG có KOL mà sản phẩm thời trang/cần người mặc): MỘT CÔ GÁI VIỆT NAM
  CỰC TRẺ, CUTE ĐÁNG YÊU — NÉT TEEN khoảng 18-20 tuổi (kiểu nữ sinh / sinh viên năm nhất, KHÔNG
  phải người mẫu), gương mặt baby bầu bĩnh dễ thương, má phinh phính, mắt to tròn, nụ cười tươi
  rạng hồn nhiên; DÁNG ĐẦY ĐẶN KHỎE KHOẮN VỪA PHẢI, CÓ DA CÓ THỊT, KHÔNG GẦY GÒ, nữ tính dễ thương;
  da trắng sáng tự nhiên (trắng hơn xíu) NHƯNG THẬT — có lỗ chân lông, KHÔNG da nhựa, KHÔNG AI quá;
  tóc đen mượt, vibe girl-next-door Gen-Z teen. TUYỆT ĐỐI KHÔNG phải người mẫu chững chạc / trên 23
  / sang chảnh / quyến rũ / gầy trơ xương.
  "very young cute teen Vietnamese girl, youthful 18-20 teen look, baby-faced, round eyes, sweet
  innocent girl-next-door, soft healthy curvy figure with some flesh, not skinny, naturally fair and
  bright but REAL natural skin with visible pores, not AI-perfect, NOT a mature/glam/professional
  fashion model".
- THỜI TRANG — MONTAGE PHỐI ĐỒ: cho nhân vật mặc sản phẩm rồi PHỐI NHIỀU OUTFIT + bối cảnh khác nhau
  (đổi áo croptop / áo phông / áo khoác / sweater + giày + phụ kiện; phòng ngủ / phố / quán cà phê...),
  ĐỔI CẢNH LIÊN TỤC bằng cắt nhanh / whoosh, mỗi look ~1-2 giây — khoe sản phẩm hợp NHIỀU phong cách.
- CẤM CHỮ TUYỆT ĐỐI trong video_prompt: thêm nguyên văn câu "Absolutely no text overlays,
  no captions, no subtitles, no on-screen graphics or rendered text of any kind." vào cuối
  video_prompt (chữ in sẵn trên bao bì/nhãn SẢN PHẨM thì giữ nguyên — đó là sản phẩm thật).
  KHÔNG đưa bất kỳ chỉ dẫn vẽ chữ nào vào video_prompt — chữ sẽ được vẽ LOCAL đè lên sau.
{overlay_rules}
- CẤM watermark, logo nền tảng (TikTok/Shopee), filter giả, khung viền."""

# Quy tắc text-overlays (V8.3-Q1 — chữ vẽ LOCAL bằng font vector, tiếng Việt CÓ DẤU thoải mái):
# overlay_policy của format quyết định danh sách bắt buộc (require) / tùy chọn (allow) / cấm (forbid).
_OVERLAY_SCHEMA = """ Mỗi mục: {"t": <giây bắt đầu, số>, "text": "<chuỗi hiện>", "pos": "top|mid|bottom",
  "kind": "hook|price|cta", "sent": <số thứ tự CÂU narration (đếm từ 0) mà chữ minh hoạ>}.
  text lấy CHÍNH XÁC từ PRODUCT_FACTS (giá/sale/số bán — TUYỆT ĐỐI không bịa); giá viết gọn
  kiểu "399K". t ước lượng = (tổng số từ các câu narration TRƯỚC câu sent)/2.8 + 0.9."""
_OVERLAY_REQUIRE = (
    """- CHỮ ĐÈ LOCAL (BẮT BUỘC): trả khóa JSON "text_overlays" gồm 1-3 mục — trong đó PHẢI có
  1 mục kind="price" với giá thật.""" + _OVERLAY_SCHEMA
)
_OVERLAY_ALLOW = (
    """- CHỮ ĐÈ LOCAL (tùy chọn): nếu giúp bán hàng, trả khóa JSON "text_overlays" tối đa 3 mục;
  không cần thì trả "text_overlays": [].""" + _OVERLAY_SCHEMA
)
_OVERLAY_FORBID = """- KHÔNG dùng chữ đè cho format này. Trả "text_overlays": []."""

# Quy tắc thoại theo chế độ audio (2026-06-11, founder chốt):
# - native (KOL nói): thoại nhúng prompt, Seedance tự đọc + lip-sync.
# - voiceover (KOL im): Seedance KHÔNG đọc tiếng Việt (model không hỗ trợ → lơ lớ) → KOL im,
#   clip chỉ có nhạc/SFX, giọng tiếng Việt ghép riêng bằng vbee → sạch, không lệch môi.
_DIALOGUE_NATIVE = (
    " + LỜI THOẠI nhúng trực tiếp trong ngoặc kép (model tự lip-sync + sinh audio)."
)
_DIALOGUE_VOICEOVER = (
    " NHÂN VẬT IM LẶNG — KHÔNG mở miệng nói, KHÔNG đọc thoại; chỉ hành động tự nhiên "
    "(cầm/nâng/xoay sản phẩm, mỉm cười, gật đầu, chỉ vào sản phẩm, nhìn camera). "
    'TUYỆT ĐỐI KHÔNG nhúng lời thoại, thêm "no speech, no talking, closed mouth" vào prompt. '
    "Clip CHỈ có nhạc nền + SFX, KHÔNG có giọng nói (giọng tiếng Việt ghép riêng sau)."
)


class DirectorResult(dict):
    """dict có khóa: storyboard, narration, image_prompts, video_prompt, cta, text_overlays."""


def write_shot_plan(
    *,
    product: dict,
    format_label: str,
    format_system_prompt: str,
    mode: str,
    seconds: int,
    kol: dict | None = None,
    user_brief: str = "",
    product_description: str = "",
    aspect: str = "9:16",
    reference_breakdown: str = "",
    formula_block: str = "",
    overlay_policy: str = "allow",
    product_facts: dict | None = None,
    voice_gender: str = "",
    kol_speaks: bool = True,
    creative_brief: dict | None = None,
) -> DirectorResult:
    """Gọi LLM sinh shot plan. Raise ``VideoEngineError`` nếu output không dùng được.

    ``product_description``: mô tả sản phẩm SIÊU CHI TIẾT do Gemini Vision bóc từ ảnh (B3) —
    nhúng vào KHỐI 2 để giữ logo/nhãn đúng. Người (KOL) luôn tả bằng TEXT, KHÔNG gửi ảnh mặt.
    V8.2 Phase 3: ``formula_block`` (few-shot từ Formula Bank), ``overlay_policy``
    (require|allow|forbid — chữ giá/sale do Seedance vẽ), ``product_facts`` (giá/sale THẬT —
    nguồn duy nhất cho chữ overlay), ``voice_gender`` (tả giọng nhân vật ở KHỐI 1).
    """
    from module2_brain.llm.v5_clients import complete_with_fallback

    aspect = "9:16"
    kol_block = ""
    if kol:
        # KOL = persona TEXT (autovis-style): model tự sinh người từ mô tả, KHÔNG có ảnh mặt đầu vào.
        kol_block = (
            f"\nNHÂN VẬT (tả bằng text trong video_prompt, KHÔNG có ảnh mặt): "
            f"{kol.get('name', '')} — {kol.get('gender', '')}, phong cách {kol.get('style', '')}. "
            f"Ngoại hình/giọng: {(kol.get('character_sheet') or '')[:700]}"
        )
    desc_block = (
        f"\nMÔ TẢ SẢN PHẨM SIÊU CHI TIẾT (DÙNG NGUYÊN cho KHỐI 2): {product_description[:900]}"
        if product_description else ""
    )
    # V8.5: CreativeBrief từ Strategist = xương sống kịch bản (góc thuyết phục + beat-plan hợp SP).
    strategy_block = ""
    if creative_brief:
        from video_engine.director.strategist import format_brief_for_director

        strategy_block = format_brief_for_director(creative_brief)
    # Luật chủ đề kênh (tông/ngách/khử-AI) đọc từ TAI-LIEU-GOC-KENH-*.md lúc chạy (fail-soft).
    from video_engine.director.channel_theme import load_channel_theme

    channel_theme = load_channel_theme()
    channel_block = (
        f"\nLUẬT CHỦ ĐỀ KÊNH (BÁM SÁT toàn bộ — định hướng tông/ngách/cách chống lộ AI của kênh):\n{channel_theme}"
        if channel_theme else ""
    )
    if channel_block:
        logger.info(f"[director] nạp chủ đề kênh ({len(channel_theme)} ký tự)")
    brief_block = f"\nGhi chú thêm từ người vận hành: {user_brief[:500]}" if user_brief else ""
    ref_block = f"\n{reference_breakdown}" if reference_breakdown else ""
    formula_part = f"\n{formula_block}" if formula_block else ""
    policy = (overlay_policy or "allow").strip().lower()
    overlay_rules = {
        "require": _OVERLAY_REQUIRE, "forbid": _OVERLAY_FORBID
    }.get(policy, _OVERLAY_ALLOW)
    facts_block = ""
    if product_facts and policy != "forbid":
        facts_block = (
            "\nPRODUCT_FACTS (nguồn DUY NHẤT cho chữ overlay — không bịa): "
            + json.dumps(product_facts, ensure_ascii=False)
        )
    # 2026-06-11: tả giọng KHỐI 1 chỉ khi native (KOL nói). Voiceover (vbee) → KOL im, không tả giọng.
    voice_line = ""
    if voice_gender and kol_speaks:
        g_en = "male" if voice_gender.strip().lower() in {"nam", "male", "m"} else "female"
        voice_line = (
            f"\n  + TẢ GIỌNG nhân vật trong KHỐI 1 (Seedance sinh giọng native + lip-sync): "
            f'vd "young Vietnamese {g_en} voice, warm energetic tone".'
        )
    dialogue_rule = _DIALOGUE_NATIVE if kol_speaks else _DIALOGUE_VOICEOVER
    # Voiceover mode (V8.3-Q3): voice đọc XUYÊN cả clip chính + đuôi CTA 6s local →
    # mật độ 48-52 từ cho 15+6s (~2.6 từ/s) đánh đủ tâm-lý-mua. Audio v2: TTS đọc
    # văn-viết-dài sẽ "đi ngang" → bắt VĂN NÓI có nhịp (câu ngắn + dấu câu dày).
    tail_s = int(settings.video_cta_tail_seconds or 0)
    # 2026-06-13 (founder: '15s = clip CHÍNH'): narration vừa CLIP CHÍNH (seconds), KHÔNG cộng đuôi
    # CTA → giọng kết thúc quanh lúc clip chính hết; đuôi CTA là outro sạch (không bị giọng tràn dài
    # gây kéo dãn khung). Trước cộng cả tail → kịch bản dài → final 20.7s cho yêu cầu 15s.
    target_words = max(10, int((seconds - 0.9) * 2.6))
    narration_hint = (
        ""
        if kol_speaks
        else (
            f"\nNARRATION = lời TỰ QUAY TỰ THOẠI kiểu CHỊ EM BÁN HÀNG TikTok/livestream — như đang TÁM "
            f"với hội bạn, khoe món MỚI SĂN ĐƯỢC rồi rủ mua. NGÔI THỨ NHẤT (xưng \"mình/tôi\"), GỌI người "
            f'xem thân mật ("mấy bà ơi", "các nàng ơi", "hội chị em ơi"). Giọng hào hứng, thân, đời '
            f"thường — TUYỆT ĐỐI KHÔNG giọng MC/TVC. "
            f"~{target_words} từ (VỪA clip chính {seconds}s, đọc ~2.6 từ/giây, chừa ~0.9s hook đầu — "
            f"đuôi CTA {tail_s}s là outro, KHÔNG kéo dài lời vào đó); bám đúng hành động nhân vật trên hình. "
            f"MẠCH: MỞ = GỌI người xem + khoe mới săn được → GIỮA = tám lý do MÊ (form/dáng/chất + tôn "
            f"dáng, hợp nhiều vóc dáng) → CUỐI = chỉ chỗ GIỎ HÀNG + rủ bấm vô coi. "
            f'VÍ DỤ GIỌNG (bám SÁT vibe này, đổi nội dung theo đúng SP): "Mấy bà ơi mấy bà ơi, tôi mới '
            f"săn được em quần này ngon lắm nè, form dáng đẹp nhỏ gọn, hợp nhiều vóc dáng, mặc lên là "
            f'tôn hết vẻ đẹp cơ thể luôn á... sản phẩm tôi để ở góc trái giỏ hàng, mấy bà bấm vô coi thử nha!" '
            f'CẤM sáo rỗng kiểu TVC ("đẳng cấp", "nâng tầm thần thái", "chân ái của mọi cô gái", "đỉnh cao"). '
            f"KHÔNG nêu lượt đã bán / số sao; KHÔNG bịa số; KHÔNG deadline giả. "
            f"Số THẬT trong PRODUCT_FACTS (giá) chỉ dùng nếu có & hợp. "
            f"BẮT BUỘC VĂN NÓI CÓ NHỊP (TTS đọc TỪNG CÂU): câu NGẮN 4-9 từ; ngắt bằng dấu chấm "
            f"(KHÔNG câu dài quá 10 từ); chen dấu phẩy chỗ ngừng lấy hơi; từ đệm tự nhiên "
            f"(nè, nha, luôn, đó, cực kỳ, đỉnh thật sự); 1 câu cảm thán hoặc hỏi tu từ. "
            f'Viết số kiểu ĐỌC ĐƯỢC: "399K" → "ba trăm chín chín ngàn". '
            f"TUYỆT ĐỐI không liệt kê khô khan kiểu thông số."
        )
    )
    prompt = (
        f"Sản phẩm: {product.get('name', '')}\n"
        f"Ngành: {product.get('category', '')}\n"
        f"Giá: {product.get('price', '')}\n"
        f"Mô tả: {(product.get('description') or '')[:800]}\n"
        f"Mode: {mode} · Format: {format_label} · Thời lượng: {seconds} giây · Tỷ lệ: {aspect}."
        f"{desc_block}{strategy_block}{channel_block}{ref_block}{formula_part}{kol_block}{brief_block}{facts_block}{narration_hint}\n"
        f"{_VIDEO_PROMPT_RULES.format(aspect=aspect, overlay_rules=overlay_rules, voice_line=voice_line, dialogue_rule=dialogue_rule)}\n"
        f"Viết shot plan JSON đúng schema đã nêu trong system prompt."
    )
    raw = complete_with_fallback(
        format_system_prompt, prompt, gemini_model=settings.gemini_model
    )
    data = _parse_json(raw)
    narration = str(data.get("narration") or "").strip()
    if not narration:
        raise VideoEngineError("Director không trả narration.")
    cleaned = _sanitize_narration(narration)
    if not cleaned:
        raise VideoEngineError(f"Narration toàn chỉ-đạo-cảnh, không dùng được: {narration[:120]}")
    if cleaned != narration:
        logger.warning("[director] narration có chỉ-đạo-cảnh → đã lọc sạch trước TTS")
    image_prompts = [str(p) for p in (data.get("image_prompts") or []) if str(p).strip()]
    video_prompt = str(data.get("video_prompt") or "").strip()
    if not video_prompt:
        raise VideoEngineError("Director không trả video_prompt.")
    video_prompt = video_prompt.replace("16:9", "9:16").replace("1:1", "9:16")
    if "9:16" not in video_prompt:
        video_prompt = "Vertical 9:16 portrait smartphone video. " + video_prompt
    # Validate cứng text_overlays — sai cấu trúc thì BỎ (không chặn job).
    # V8.3-Q1: thêm kind (hook|price|cta) + sent (index câu narration, dùng đồng bộ Q2b).
    overlays = []
    for item in (data.get("text_overlays") or [])[:3]:
        if isinstance(item, dict) and str(item.get("text") or "").strip():
            sent_raw = str(item.get("sent", "")).strip()
            overlays.append(
                {
                    "t": str(item.get("t") or "").strip(),
                    "text": str(item.get("text") or "").strip()[:40],
                    "pos": str(item.get("pos") or "").strip(),
                    "kind": str(item.get("kind") or "").strip().lower(),
                    "sent": int(sent_raw) if sent_raw.isdigit() else None,
                }
            )
    if policy == "forbid" and overlays:
        logger.warning("[director] overlay_policy=forbid nhưng LLM trả text_overlays → bỏ")
        overlays = []
    if policy == "require" and not overlays and (product_facts or {}).get("price"):
        # LLM lờ yêu cầu → chèn GIÁ mặc định từ data thật (deterministic — không phụ thuộc LLM).
        overlays = [{
            "t": str(round(max(2.0, seconds * 0.6), 1)),
            "text": str(product_facts["price"]), "pos": "bottom", "kind": "price", "sent": None,
        }]
        logger.warning("[director] policy=require nhưng LLM không trả overlay → thêm giá mặc định")
    return DirectorResult(
        storyboard=data.get("storyboard") or [],
        narration=cleaned,
        image_prompts=image_prompts[:2],
        video_prompt=video_prompt,
        cta=str(data.get("cta") or "").strip(),
        text_overlays=overlays,
    )


def _parse_json(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        data = json.loads(text)
    except ValueError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise VideoEngineError(f"Director trả output không phải JSON: {text[:200]}") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise VideoEngineError("Director JSON không phải object.")
    return data


def _sanitize_narration(narration: str) -> str:
    """Bỏ mọi mảnh chỉ-đạo-cảnh để TTS không đọc nhầm (giữ câu văn tự nhiên)."""
    cleaned = _BANNED_NARRATION.sub(" ", narration)
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)  # bỏ chú thích trong ngoặc tròn
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned
