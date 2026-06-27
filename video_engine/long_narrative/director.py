"""director.py — LLM Director long-form: topic/tin → kịch bản JSON V2 (cà khịa) + SEO.

Một call Gemini text (reuse `complete_with_fallback` như strategist): nhận chủ đề + nguồn tin
(fact-grounded chống bịa) → kịch bản news-entertainment kiểu Lóng/Đức/Thanh Pahm: nhiều beat,
giọng cà khịa, QUAN ĐIỂM GỐC (lá chắn 'inauthentic' của YouTube — Section J3), biến thiên cấu trúc.

Trả `LongformScript` (beats V2 + meta SEO) hoặc None (fail-soft). Caption/giọng/ảnh do engine lo.
"""

from __future__ import annotations

import json
import re

from config.settings import settings
from core.logger import logger
from video_engine.long_narrative.critic import AI_FILLER  # nguồn cấm-từ-đệm dùng chung (DRY)
from video_engine.long_narrative.script_schema import LongformScript

_VALID_CTX = "normal|hype|joke|climax|whisper|drama"

_SYSTEM = (
    "Bạn là biên kịch kênh YouTube 'điểm tin - giải trí' tiếng Việt, cùng trường phái Vui Vẻ / Lóng: "
    "một THẰNG BẠN THÔNG MINH MÀ LẦY ngồi BUÔN CHUYỆN cho hội bạn nghe — nắm kiến thức chắc, kể tuyến "
    "tính rõ, NHƯNG liên tục chêm cà khịa, ví von game/đời thường, slang Gen-Z để hạ tông học thuật "
    "xuống mức 'ngồi tám với nhau'. KHÔNG đọc bản tin, KHÔNG giọng giảng bài.\n"
    "XƯNG HÔ (xương sống nhận diện — BẮT BUỘC dùng, ĐỪNG né): kéo người xem làm ĐỒNG BỌN — 'chúng ta' "
    "('hôm nay chúng ta sẽ nói về...', 'chúng ta cùng nhìn lại'), 'anh em' (gọi thân, ấm: 'anh em biết "
    "gì không', 'anh em yên tâm'), 'các bạn' (ở disclaimer + dặn dò). Tự xưng 'tôi' khi nêu quan điểm/"
    "trải nghiệm ('tôi nghĩ là', 'tôi cũng không chắc'). Đây KHÔNG phải thảo mai. "
    "CHỈ CẤM biến thể NŨNG NỊU lên gân: kéo dài âm ('bạn ơiii', 'mấy ông ơi', 'anh em ơi'), nịnh ('đúng "
    "không nào', 'đúng không bạn', 'nha bạn', 'nè bạn').\n"
    "GỌI NHÂN VẬT suồng sã như người quen, nhưng VẪN có connector trôi quanh tên (đừng bỏ trơ tên rồi "
    "chấm cụt): 'ông này', 'ông chú', 'mấy bố này', 'thằng cha', 'con này', 'cái bọn'; được Việt-hoá/chế "
    "tên cho vui ('độc tài Mbappé', 'bố già Perez').\n"
    "NHỊP CÂU: câu DÀI CUỘN NHIỀU MỆNH ĐỀ là MẶC ĐỊNH — nối bằng 'thì / ấy / đấy / nên là / cơ mà / "
    "thế là / mà', đọc liền một hơi như đang nói. Câu cực ngắn ('Toang.', 'Căng.', 'Hay phết.', 'Chắc "
    "không cay đâu.') chỉ là GIA VỊ — rải THƯA để PUNCH, đừng câu nào cũng cụt.\n"
    "HÀI rải SUỐT dòng kể (không dồn vào cú chốt lạnh): ví von bậy-mà-duyên gắn vào sự kiện nghiêm túc, "
    "nhập vai/lồng tiếng nhân vật bằng slang game ('múc bang', 'Aura Farming', 'check map'), tự cà khịa "
    "mình / phá vai ('tôi cũng không chắc có thật hay chỉ bốc phét'), chêm aside cảm thán ('Khiếp', 'Mẹ').\n"
    "KHIÊM TỐN về độ tin: được rào 'tôi cũng không biết có thật không', 'chỉ là lời đồn', 'tham khảo giải "
    "trí thôi' — ĐỪNG phán như đúng rồi.\n"
    "VIẾT ĐỂ NÓI (văn nói trôi chảy), KHÔNG dùng từ đệm máy móc kiểu AI. CHỈ trả JSON thuần, không markdown."
)


def _rubric(n_beats: int, visual_mode: str = "doodle") -> str:
    # Trường ảnh trong schema beat đổi theo visual_mode: photo_meme/hybrid cần entity ảnh thật + nhãn meme;
    # doodle cần mô tả caricature. (image_source 'news' đánh dấu beat ưu tiên tư liệu thật.)
    if visual_mode in ("photo_meme", "hybrid"):
        img_lines = (
            '     "image_source": "news",\n'
            '     "photo_subject": "Để tra ẢNH THẬT trên Wikimedia (nguồn quốc tế): tên RIÊNG cầu thủ giữ nguyên (vd \'Cristiano Ronaldo\', \'Lionel Messi\'); tên đội/CLB ghi TIẾNG ANH (vd \'Argentina national football team\', \'Portugal national football team\', \'Real Madrid CF\'). Rỗng nếu beat thuần cảm xúc/cà-khịa.",\n'
            '     "meme_tags": ["1-2 nhãn cảm xúc/cà-khịa TIẾNG VIỆT (vd ăn mừng, troll trọng tài, thất vọng) để khớp meme"],'
        )
        img_rule = ("\n- HÌNH (mode ảnh thật + meme): mỗi beat điền photo_subject (entity có ảnh thật) VÀ/HOẶC "
                    "meme_tags (cảm xúc). Beat sự kiện → photo_subject; beat cà-khịa/drama/climax → meme_tags. KHÔNG cần img_prompt.")
    else:  # doodle
        img_lines = (
            '     "image_source": "ai",\n'
            '     "img_prompt": "tả 1 cảnh CARICATURE hoạt hình (countryball/nhân vật mặt biểu cảm), thick black outlines, no text — minh hoạ beat",\n'
            '     "broll_keywords": ["2 từ khoá footage TIẾNG ANH cho Pexels (vd stadium crowd, news studio)"],'
        )
        img_rule = ""
    banned = ", ".join(f'"{w}"' for w in AI_FILLER)
    return f"""Trả DUY NHẤT 1 JSON object đúng schema:
{{
 "title": "tiêu đề video hấp dẫn (tiếng Việt)",
 "seo": {{"titles": ["3 tiêu đề YouTube giật nhẹ"], "description": "mô tả 2-3 câu + nguồn + 3-5 hashtag", "tags": ["10-15 tag"]}},
 "beats": [
   {{
     "label": "NHÃN NGẮN IN HOA BÁM CHỦ ĐỀ beat (đừng chép nguyên ví dụ; vd thể thao: TRANH CÃI, KỶ LỤC; thần thoại: TRUYỀN THUYẾT, BÍ ẨN)",
     "callout": "CALLOUT TO IN HOA ≤6 TỪ (điểm nhấn beat)",
     "context": "{_VALID_CTX} (cảm xúc beat → quyết nhạc/nhịp)",
{img_lines}
     "narration_blocks": [
       {{"speaker": "narrator", "text": "lời kể TRÔI, cuộn nhiều mệnh đề, đời thường + cà khịa + quan điểm gốc", "context": "..."}}
     ]
   }}
 ]
}}

QUY TẮC BẮT BUỘC:
- Đúng {n_beats} beat. Beat ĐẦU = MỞ THÂN MẬT: cho phép vào bài bằng disclaimer-mở ("Và như mọi khi thì những thông tin trong video chúng tôi tổng hợp và cóp nhặt từ nhiều nguồn, có gì sai anh em comment bên dưới") + "hôm nay chúng ta sẽ nói về..." HOẶC câu hỏi gài-tò-mò DÀI rồi tự trả lời HOẶC quan sát đời thường ngôi-1. KHÔNG bắt buộc ném số sốc; KHÔNG mở khô khan kiểu bản tin. Beat CUỐI = CTA đời thường: "anh em thấy sao thì comment bên dưới" + rủ like/đăng ký kênh + câu hỏi tranh luận. CTA CHỈ MỘT lần ở cuối (đừng lặp 2 đoạn outro); TUYỆT ĐỐI KHÔNG nêu/bịa TÊN kênh cụ thể (đừng tự chế "kênh ABC", "La La School"...) — chỉ nói chung "đăng ký kênh"; KHÔNG dùng từ Anh "subscribe" (nói "đăng ký").
- FACT-GROUNDING: chỉ dùng số liệu/sự kiện CÓ trong NGUỒN TIN bên dưới. KHÔNG bịa số/tên/kết quả. Không chắc thì nói chung chung HOẶC rào thẳng ("cái này tôi cũng không chắc lắm").
- XƯNG HÔ ĐỒNG BỌN (BẮT BUỘC, đây là chất kênh): dùng "chúng ta / anh em / các bạn" thoải mái như đời thật (vài lần mỗi beat là bình thường). Tự xưng "tôi" khi nêu quan điểm. CHỈ tránh biến thể nũng nịu kéo âm ("...ơiii", "đúng không nàooo").
- DNA NHỊP (BẮT BUỘC — bám đúng Vui Vẻ/Lóng): câu DÀI CUỘN NHIỀU MỆNH ĐỀ là MẶC ĐỊNH, nối bằng "thì / ấy / đấy / nên là / cơ mà / thế là / mà", đọc liền một hơi. Câu cực ngắn chốt ("Toang.", "Căng.", "Hay phết.", "Chắc không cay đâu.") chỉ rải THƯA — tối đa ~1 câu chốt sau mỗi 3-4 câu dài, KHÔNG phải mỗi beat 2 câu cụt. Nhịp đúng = TRÔI rồi mới NGẮT, không phải NGẮT-NGẮT-NGẮT.
- CONNECTOR đặc trưng RẢI DÀY (chất văn-nói): "thì" (chêm giữa mệnh đề), "ấy / đấy" (chốt mệnh đề), "nên là" (nhân-quả), "cơ mà" (bẻ ý), "thế là" (kể tiếp diễn biến), "tức là / nói đơn giản thì / hiểu đơn giản là" (diễn giải dân dã), "kiểu / kiểu như là" (so sánh đời thường).
- HÀI rải SUỐT dòng kể, KHÔNG dồn vào cú chốt lạnh: (1) ví von BẬY-mà-duyên gắn vào sự kiện nghiêm túc; (2) nhập vai/lồng tiếng nhân vật bằng slang game ("múc bang", "Aura Farming", "check map", "dùng phù thủy cấp quân"); (3) tự cà khịa mình / phá vai ("tôi cũng không chắc có thật hay chỉ bốc phét thôi"); (4) chêm aside cảm thán giữa dòng ("Khiếp", "Mẹ", "Hai phết"). ĐỪNG diễn giải khô — hãy SO SÁNH cái khó với đồ đời thường / game / phim.
- SLANG đời thường ĐÚNG ngữ cảnh (đừng nhồi): toang, gáy, ăn hành, bay màu, múc, no hope, húp, rén, carry, gánh team, tèo, về bờ, đứng hình, vip pro. CHO PHÉP particle đời thật 2 kênh: "thú thật là", "anh em cứ tưởng tượng", "nói chung là", "nói cách khác là" — đây là khẩu ngữ của họ, KHÔNG phải filler máy.
- CẤM cụm máy móc kiểu AI: {banned}. Cũng TRÁNH liệt kê khô ("đầu tiên/tiếp theo/cuối cùng") + sáo rỗng ("quả là", "một điều thú vị") + từ tự-chế sến ("U là trời", "Ảo thật sự").
- ĐỪNG kết câu bằng tic lặp "đó"/"nè"/"đấy" ("...thôi đó", "...đó đó", "...nè nè") — chêm particle này THƯA.
- CONTEXT mỗi block PHẢI biến thiên theo cảm xúc THẬT (normal|hype|joke|climax|whisper|drama) — đừng để mọi block cùng một context.
- BIẾN THIÊN cấu trúc/độ dài beat, đừng lặp khuôn. Có lời thoại nhân vật thì TÁCH block speaker riêng (speaker != 'narrator') để engine đọc giọng khác — nhập vai.
- narration_blocks đọc NGUYÊN ĐOẠN (đọc liền hơi), KHÔNG chẻ vụn.{img_rule}
- MỖI BEAT = 1 MẠCH KỂ (~20-32 giây đọc) cuộn nhiều mệnh đề móc nối — ĐỪNG chẻ vụn 1 ý thành nhiều beat cụt; kể trôi như buôn chuyện, đổi beat khi đổi Ý chứ không phải đổi câu.
- MẪU GIỌNG ĐÚNG (bám đúng nhịp/xưng-hô 2 kênh — bắt chước CÁI NÀY):
  [Vui Vẻ — ví von bậy + trôi]: "Tương truyền mấy con Garuda này hàng ngày nó múc bang tới cả vài trăm con Naga, cái này tôi nghĩ là người xưa thấy chim ăn nhiều rắn nhỉ, thế là ngon sáng tác ra cho oách luôn."
  [Vui Vẻ — đồng bọn + chốt thưa]: "Và anh em biết gì không, một ông chú gần 38 tuổi mà vào sân là biến cả đội Algeria thành bài khởi động luôn, ba bàn một mình, thế là giờ này Algeria chắc đang họp khẩn mặt nặng như chì. Toang."
  [Lóng — câu dài cuộn nhiều mệnh đề]: "Thì Mỹ đánh thuế Trung Quốc để bảo vệ sản xuất trong nước, nhưng mà Trung Quốc cũng bóp được nguồn cung đất hiếm để bóp nghẹt lại, tức là trong câu chuyện này thì Mỹ đấm Trung Quốc cũng không khác gì đang tự đấm mình."
  [Lóng — số sốc dịch sang đời thường + cà khịa tỉnh]: "Giá căn hộ Hà Nội tăng hơn 70% trong khi lương thì nhúc nhích 6-8% một năm, nói đơn giản là anh em làm quần quật cả tháng thực chất cũng chỉ đang làm công cho ông chủ bất động sản thôi."
  MẪU SAI (CẤM): cụt-lủn khẩu hiệu "Messi. 38 tuổi. Ba bàn. Một mình. Toang." | nũng nịu kéo âm "Mấy ông ơiii đỉnh lắm luôn á, đúng không nào!"
- Tiếng Việt đời thường, hài, dụ xem tới cuối. Tổng lời ~{n_beats * 55}-{n_beats * 95} từ."""


def _parse(raw: str) -> dict | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        data = json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except ValueError:
            return None
    if not isinstance(data, dict) or not (data.get("beats")):
        return None
    return data


_CTA_PUNCT = ".,!?:;"


def _sanitize_cta(text: str) -> str:
    """Chặn 2 lỗi LLM hay tự chế ở CTA dù prompt đã cấm: (1) từ Anh 'subscribe' → 'đăng ký'; (2) BỊA tên
    kênh sau chữ 'kênh' (vd 'kênh La La School' → 'kênh') — kênh thật còn placeholder nên CTA để chung.
    Dùng str.isupper() theo TỪNG TỪ (KHÔNG dải regex À-Ỹ — dải đó gồm cả chữ thường VN → nuốt nhầm 'để')."""
    if not text:
        return text
    out = re.sub(r"\bsubscribe\b", "đăng ký", text, flags=re.IGNORECASE)
    toks = out.split(" ")
    res: list[str] = []
    i = 0
    while i < len(toks):
        cur = toks[i]
        res.append(cur)
        i += 1
        if cur.lower() != "kênh":            # chỉ xử khi token ĐÚNG là 'kênh' (không dính dấu câu → cùng câu với tên)
            continue
        while i < len(toks) and toks[i][:1].isupper():   # bỏ các TỪ VIẾT HOA liền sau = tên kênh LLM bịa
            ended = toks[i][-1:] in _CTA_PUNCT
            i += 1
            if ended:                        # tên kết thúc câu/cụm → dừng, không ăn sang phần sau
                break
    return " ".join(res)


def generate_script(
    topic: str, category: str = "", *, source_text: str = "", n_beats: int | None = None,
    feedback: str = "", visual_mode: str = "doodle",
) -> LongformScript | None:
    """topic/tin (+ nguồn) → LongformScript V2. None nếu LLM/JSON lỗi (caller xử fail-soft).

    `feedback` (gợi ý critic vòng trước) → chèn vào prompt để VIẾT LẠI tốt hơn (critic loop).
    `visual_mode` đổi schema ảnh trong rubric: photo_meme/hybrid → photo_subject+meme_tags; doodle → img_prompt.
    """
    from core.config_checks import looks_real_secret
    if not looks_real_secret(settings.gemini_api_key or "") and not looks_real_secret(settings.groq_api_key or ""):
        logger.warning("[director] thiếu key LLM → không sinh kịch bản")
        return None

    n = n_beats or 8
    src = (source_text or "").strip()[:6000]
    src_block = f"\nNGUỒN TIN (fact-ground, chỉ dùng dữ kiện ở đây):\n{src}\n" if src else "\n(Không có nguồn — kể tổng quát, KHÔNG bịa số cụ thể.)\n"
    fb_block = ""
    if (feedback or "").strip():
        fb_block = (
            "\n⚠️ VIẾT LẠI THEO GÓP Ý CRITIC (giữ ĐÚNG fact, tăng hài/cà-khịa/hook/CTA, đừng lặp lỗi cũ):\n"
            + feedback.strip() + "\n"
        )
    user = (
        f"CHỦ ĐỀ: {topic}\nTHỂ LOẠI: {category or 'tin tức - giải trí'}\n{src_block}{fb_block}\n"
        + _rubric(n, visual_mode)
    )
    try:
        from module2_brain.llm.v5_clients import complete_with_fallback
        raw = complete_with_fallback(_SYSTEM, user, gemini_model=settings.gemini_model)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[director] LLM lỗi: {str(exc)[:200]}")
        return None

    data = _parse(raw)
    if data is None:
        logger.warning("[director] output không phải JSON V2 dùng được")
        return None
    for _beat in (data.get("beats") or []):              # vệ sinh CTA: bỏ 'subscribe' + tên kênh LLM bịa
        for _blk in (_beat.get("narration_blocks") or []):
            if isinstance(_blk, dict) and _blk.get("text"):
                _blk["text"] = _sanitize_cta(_blk["text"])
    data.setdefault("category", category)
    script = LongformScript.from_obj(data)
    # gắn SEO vào meta để dashboard/upload dùng
    if isinstance(data.get("seo"), dict):
        script.meta["seo"] = data["seo"]
    logger.info(f"[director] '{topic[:40]}' → {len(script.beats)} beat, {script.total_chars} ký tự")
    return script if script.beats else None


def suggest_topics(category: str, n: int = 5) -> list[dict]:
    """Gợi ý n chủ đề video từ RSS theo category (LLM biến headline thành góc cà khịa). Fail-soft."""
    from video_engine.long_narrative.ingest import fetch_rss_headlines
    heads = fetch_rss_headlines(category, limit=12)
    if not heads:
        return _brainstorm_topics(category, n)  # thể loại thường-xanh (lịch sử/thần thoại) → LLM nghĩ
    raw_list = [{"title": h["title"], "summary": h["summary"], "link": h["link"]} for h in heads[:n]]
    try:
        from core.config_checks import looks_real_secret
        if not looks_real_secret(settings.gemini_api_key or ""):
            return raw_list
        from module2_brain.llm.v5_clients import complete_with_fallback
        head_block = "\n".join(f"- {h['title']}" for h in heads[:12])
        user = (
            f"Từ các tin '{category}' dưới đây, chọn {n} tin HẤP DẪN nhất để làm video cà khịa. "
            "Với mỗi tin trả 1 tiêu đề video giật nhẹ + độ nóng. CHỈ trả JSON: "
            '{"topics":[{"title":"...","angle":"góc cà khịa 1 câu","hot":"cao|vừa|thấp"}]}\n\n'
            + head_block
        )
        raw = complete_with_fallback(_SYSTEM, user, gemini_model=settings.gemini_model)
        data = _parse_obj(raw)
        topics = (data or {}).get("topics") or []
        out = [t for t in topics if isinstance(t, dict) and t.get("title")][:n]
        return out or raw_list
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[director] suggest_topics fail-soft → headline thô: {str(exc)[:120]}")
        return raw_list


def _brainstorm_topics(category: str, n: int = 5) -> list[dict]:
    """Thể loại THƯỜNG-XANH (lịch sử/thần thoại/kiến thức — không có RSS tin mới) → LLM nghĩ n chủ đề
    video cà khịa từ kiến thức nền. Fail-soft → []."""
    from core.config_checks import looks_real_secret
    if not looks_real_secret(settings.gemini_api_key or "") and not looks_real_secret(settings.groq_api_key or ""):
        return []
    try:
        from module2_brain.llm.v5_clients import complete_with_fallback
        user = (
            f"Nghĩ {n} chủ đề video YouTube giải trí CÀ KHỊA thuộc mảng '{category}' (thường-xanh, "
            "KHÔNG cần tin mới — lấy từ kiến thức/câu chuyện hay). Mỗi chủ đề 1 góc lạ, gây tò mò. "
            'CHỈ trả JSON: {"topics":[{"title":"tiêu đề giật nhẹ","angle":"góc cà khịa 1 câu","hot":"cao|vừa|thấp"}]}'
        )
        raw = complete_with_fallback(_SYSTEM, user, gemini_model=settings.gemini_model)
        data = _parse_obj(raw)
        return [t for t in ((data or {}).get("topics") or []) if isinstance(t, dict) and t.get("title")][:n]
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning(f"[director] brainstorm topics '{category}' fail: {str(exc)[:120]}")
        return []


def _parse_obj(raw: str) -> dict | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    try:
        return json.loads(text)
    except ValueError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                return None
    return None
