"""shot_planner.py — ĐẠO DIỄN HÌNH (LLM): beat + blocks → list[ShotSpec] (chỉ enum + ý đồ).

Triết lý "sáng tạo nhưng trong khuôn": LLM CHỌN MÓN từ menu enum + tả ý đồ (query/hint), KHÔNG tự ra
toạ độ/z-index/giây/tên-file. Mọi thứ không-gian do shot_builder tính tất định. Chống làm bừa = 4 lớp:
(1) menu enum đóng + nhồi rubric vào prompt; (2) CRITIC chấm điểm + regen 1 lần; (3) validate_and_repair
COERCE enum sai về default (không reject — giữ phần tốt); (4) hỏng cấu trúc → trả [] → caller fallback look cũ.

shot_planner QUYẾT, KHÔNG đụng asset/MoviePy/toạ độ. Tái dùng complete_with_fallback + pattern _parse của director.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from config.settings import settings
from core.logger import logger

# ── MENU enum (nguồn chân lý dùng chung cho validate + critic + builder) ──────
VALID_TRANSITIONS = {"cut", "fade", "glitch"}
# glitch/tv_static BỎ khỏi content (colorbar 2s chói) — biến động/sốc giờ vẽ DOODLE hỗn loạn + flash glitch ở transition_in.
VALID_CONTENT_KINDS = {"real_photo", "logo", "screenshot", "map", "diagram", "meme",
                       "doodle", "terminal", "countryball"}
VALID_CONTENT_MOTION = {"slide_in_left", "slide_in_right", "pop_in", "zoom_in", "zoom_out", "static", "shake"}
VALID_ROLES = {"subject", "reaction", "accent"}
VALID_SIDES = {"left", "right", "center"}
VALID_PRESENTER_MOTION = {"static", "rise_in", "pop_in"}
VALID_POSE_HINTS = {"point", "celebrate", "shock", "laugh", "think", "explain", "smug", "worry"}  # 6.1
# glitch_interstitial BỎ (full-shot colorbar 2s quá chói) — glitch giờ CHỈ là FLASH 0.12s ở transition_in.
VALID_LAYOUTS = {"presenter_hero", "presenter_corner", "object_center", "side_by_side",
                 "fullbleed_scene", "icon_grid", "terminal_fullbleed"}

_SEC_PER_SHOT = 2.5          # nhịp ~2-3s/shot (founder chốt) → số shot mục tiêu mỗi đoạn
_CRITIC_THRESHOLD = 7.0      # điểm < ngưỡng → regen 1 lần
_GLITCH_CAP = 0.20           # ≤20% transition là glitch (chống ức chế thị giác)


@dataclass
class ShotSpec:
    """1 quyết định dựng-hình của đạo diễn (CHƯA có asset/toạ độ). seg = đoạn nói (block) nó minh hoạ."""
    seg: int = 0
    transition_in: str = "cut"
    duration_weight: float = 1.0
    layout: str = "presenter_corner"       # KIỂU BỐ CỤC (chống đơn điệu) — xem VALID_LAYOUTS
    content: dict = field(default_factory=lambda: {"kind": "doodle", "query": "", "entity": "", "hint": ""})
    content_motion: str = "static"
    presenter: dict | None = None          # {role, side, motion, pose_hint} hoặc None (B-roll thuần)
    text: dict | None = None               # {label} hoặc None


# ── prompt: nhồi rubric + ngữ pháp kênh + few-shot (front-load để bản đầu đã chất) ──
_SYSTEM = (
    "Bạn là ĐẠO DIỄN HÌNH của kênh 'điểm tin cà khịa' kiểu Vui Vẻ/Lóng. Việc của bạn: chọn cách DỰNG HÌNH "
    "cho từng nhịp kể. BẠN CHỈ ĐƯỢC CHỌN TỪ MENU (enum) + tả Ý ĐỒ (query/hint) — TUYỆT ĐỐI KHÔNG tự nghĩ "
    "toạ độ, KHÔNG đặt thời lượng giây, KHÔNG đặt thứ tự lớp, KHÔNG bịa tên file. Phong cách: màu PHẲNG, viền "
    "đen dày, KHÔNG bóng/gradient, nhịp tĩnh-nhấn-tĩnh, cắt nhanh ~2-3s/cảnh.\n"
    "⭐⭐ CHIẾN LƯỢC HÌNH (BÁM ĐÚNG KÊNH GỐC — quan trọng nhất): NGƯỜI DẪN MỘT MÌNH (đổi cảm-xúc/pose theo lời) "
    "là HÌNH CHÍNH, xương sống kênh — chiếm ~55-60% shot (presenter role=subject/reaction, content.kind có thể "
    "rỗng hoặc 1 icon nhỏ). Phần còn lại = B-roll ĐƠN GIẢN khớp đúng vật đang nói: 1 icon/đồ-vật (cúp, bóng, "
    "thẻ, file, logo), 1 countryball, 1 ảnh thật biểu-tượng, 1 màn terminal, 1 meme phản-ứng. ĐỪNG vẽ doodle "
    "CẢNH PHỨC TẠP (kênh gốc KHÔNG vẽ cảnh cầu kỳ — chỉ icon đơn giản + người dẫn). Doodle chỉ khi không có "
    "icon/ảnh/logo phù hợp, và vẽ 1 CHỦ THỂ ĐƠN GIẢN.\n"
    "RUBRIC TỰ KIỂM (đạt cả 5 mới tốt): 1) CHẤT LIỆU khớp nội dung đang nói; 2) NHỊP nhanh ~2-3s + đa dạng; "
    "3) NGƯỜI DẪN ~55-60% shot (hình CHÍNH), MỖI lần 1 pose/cảm-xúc KHÁC, KHÔNG phủ liên tục >2 shot; "
    "4) CHUYỂN ĐỘNG khớp cảm xúc (sốc→shake/pop, kể→slide/static); 5) KHÔNG lặp khuôn, KHÔNG cảnh phức tạp.\n"
    "LUẬT CHẤT LIỆU (1 chất/shot, KHÔNG trộn): CẦU THỦ / KHOẢNH KHẮC TRẬN ĐẤU → 'doodle' (VẼ caricature "
    "cường điệu HÀI đúng phong cách kênh — TUYỆT ĐỐI KHÔNG 'real_photo' cho cầu thủ/trận đấu vì ảnh thật "
    "hay LẠC sang trận CŨ/khác + sai nét vẽ); quốc gia/đội → 'countryball' (cục cờ mặt cảm xúc); máy tính/"
    "hack/virus → 'terminal'; công ty/giải đấu → 'logo'; khái niệm/ví von đời thường → 'doodle'; web → "
    "'screenshot'; bản đồ/mạng lưới → 'map'/'diagram'; biến động/sốc/lỗi → 'doodle' vẽ cảnh hỗn loạn/nổ "
    "(ĐẶT transition_in='glitch' để có flash nhiễu ngắn); cà-khịa cảm xúc → 'meme'. 'real_photo' CHỈ dùng "
    "cho nhân vật/sự kiện NGOÀI bóng đá có ảnh BIỂU TƯỢNG thật.\n"
    "HÀI HÌNH: hint cho doodle nên gợi cảnh CƯỜNG ĐIỆU buồn cười để hút view (vd 'ông cụ Messi chống gậy "
    "vẫn sút tung lưới', 'thủ môn Algeria khóc thét bay người'), không tả khô.\n"
    "⭐ ĐA DẠNG NỘI DUNG (QUAN TRỌNG NHẤT — chống nhàm, founder than 'toàn 1 ảnh'): MỖI shot 1 CHỦ THỂ/GÓC "
    "KHÁC. TUYỆT ĐỐI KHÔNG nhiều shot cùng 1 cảnh (CẤM kiểu 5 shot đều 'Messi chỉ tay Ronaldo'). Cùng 1 "
    "chủ đề phải XOAY nhiều góc: cận 1 nhân vật / cảnh hành động (sút, ăn mừng, ngã, gãy) / đám đông fan gào "
    "/ CÚP-đồ vật cận cảnh / countryball đội / THỐNG KÊ (diagram VS) / MEME phản ứng (cười-khóc-sốc) / người "
    "dẫn cà khịa. TRỘN kind xen kẽ: doodle + meme + countryball + diagram + object — KHÔNG để toàn doodle 1 "
    "kiểu. Nhồi shot 'meme' (phản ứng hài) rải đều để hút view.\n"
    "TRANSITION: phần lớn 'cut'; 'glitch' chỉ ở khúc BẺ LỚN (≤1/5 shot); 'fade' ở cuối đoạn.\n"
    "LAYOUT (chọn 1/shot — ĐỔI LUÂN PHIÊN, KHÔNG quá 2 shot liền cùng layout, đây là cách CHỐNG ĐƠN ĐIỆU): "
    "'presenter_hero'=người dẫn TO giữa khi ĐỘC THOẠI/mở-bài/chốt/cảm-thán (không cần content); "
    "'presenter_corner'=người dẫn nhỏ góc phản ứng khi có ảnh/doodle là chủ thể; "
    "'object_center'=1 vật/logo/icon giữa, KHÔNG người dẫn (giới thiệu 1 thứ); "
    "'fullbleed_scene'=cảnh phủ KÍN khung (bối cảnh/sân/địa-điểm/lịch-sử); "
    "'icon_grid'=lặp icon thành lưới khi nói SỐ-NHIỀU/lan-rộng (nhiều đội, đám đông); "
    "'terminal_fullbleed'=màn đen/code; 'side_by_side'=chia đôi khi SO SÁNH 2 thứ (glitch là FLASH ngắn ở "
    "transition_in, KHÔNG phải 1 shot riêng). ĐA DẠNG layout là điểm số #6 của rubric.\n"
    "KHUNG HÌNH (ghi RÕ vào content.hint cho HỢP cảnh — ĐỪNG đồng loạt 1 kiểu, đó là đơn điệu): 'bán thân' "
    "(đầu→bụng) cho nhân vật NÓI/PHẢN ỨNG/biểu cảm (nét chủ đạo kênh); 'toàn thân' cho HÀNH ĐỘNG (sút bóng, "
    "nhảy ăn mừng, chạy, ngã); 'toàn cảnh/góc rộng' cho BỐI CẢNH/sân/đám đông; 'cận cảnh' cho ĐỒ VẬT (cúp, "
    "bóng, logo, thẻ đỏ). Mỗi hint NÊU RÕ khung hình + nội dung (vd 'bán thân ông già Messi gào ăn mừng', "
    "'toàn cảnh sân vận động nổ tung', 'cận cảnh chiếc cúp vàng').\n"
    "CHỈ trả JSON thuần, không markdown."
)

_FEWSHOT = """VÍ DỤ (BÁM KÊNH GỐC: NGƯỜI DẪN 1 mình là chính, đổi pose mỗi shot; B-roll ĐƠN GIẢN 1-vật. Đừng chép chữ):
{"plan":"Người dẫn dẫn dắt + phản ứng xuyên suốt; xen icon/cúp/countryball/meme đơn giản đúng lời.",
 "shots":[
  {"seg":0,"transition_in":"cut","duration_weight":1.0,"layout":"presenter_hero","content":{"kind":"doodle","query":"","entity":"","hint":""},"content_motion":"static","presenter":{"role":"subject","side":"center","motion":"rise_in","pose_hint":"explain"},"text":{"label":"AI LÀ GOAT?"}},
  {"seg":0,"transition_in":"cut","duration_weight":0.9,"layout":"object_center","content":{"kind":"doodle","query":"simple gold trophy icon","entity":"","hint":"icon ĐƠN GIẢN cận cảnh chiếc cúp vàng"},"content_motion":"pop_in","presenter":null,"text":null},
  {"seg":0,"transition_in":"cut","duration_weight":1.0,"layout":"presenter_corner","content":{"kind":"countryball","query":"Argentina countryball jumping","entity":"Argentina","hint":"countryball Argentina nhảy cẫng"},"content_motion":"pop_in","presenter":{"role":"reaction","side":"right","motion":"static","pose_hint":"celebrate"},"text":null},
  {"seg":1,"transition_in":"cut","duration_weight":1.0,"layout":"presenter_hero","content":{"kind":"doodle","query":"","entity":"","hint":""},"content_motion":"static","presenter":{"role":"subject","side":"center","motion":"static","pose_hint":"smug"},"text":null},
  {"seg":1,"transition_in":"cut","duration_weight":0.9,"layout":"object_center","content":{"kind":"meme","query":"laughing meme face","entity":"","hint":"MEME mặt cười ngất cường điệu"},"content_motion":"pop_in","presenter":null,"text":null},
  {"seg":1,"transition_in":"cut","duration_weight":1.0,"layout":"presenter_hero","content":{"kind":"doodle","query":"","entity":"","hint":""},"content_motion":"static","presenter":{"role":"subject","side":"center","motion":"static","pose_hint":"shock"},"text":{"label":"TRỜI ƠI!"}},
  {"seg":1,"transition_in":"cut","duration_weight":1.0,"layout":"side_by_side","content":{"kind":"diagram","query":"Messi vs Ronaldo","entity":"","hint":"Messi vs Ronaldo"},"content_motion":"static","presenter":{"role":"reaction","side":"right","motion":"static","pose_hint":"think"},"text":{"label":"AI HƠN?"}}
 ]}"""


def _user_prompt(beat, segments: list, n_target: int) -> str:
    seg_lines = []
    for i, (_st, sd, bi) in enumerate(segments):
        txt = ""
        if beat.narration_blocks and bi < len(beat.narration_blocks):
            txt = (beat.narration_blocks[bi].text or "")[:110]
        seg_lines.append(f'  đoạn {i} (~{sd:.1f}s): "{txt}"')
    segs = "\n".join(seg_lines)
    return (
        f"BEAT: nhãn='{beat.label}' callout='{beat.callout}' cảm-xúc={beat.context}\n"
        f"CÁC ĐOẠN NÓI (chia sẵn — mỗi shot phải gắn 'seg' = số đoạn nó minh hoạ; nội dung shot KHỚP lời đoạn):\n{segs}\n"
        "⛔⛔ LUẬT SỐ 1 (founder than 'video TOÀN 1 ẢNH 2 người đối đầu'): MỖI content.hint chỉ tả 1 CHỦ THỂ "
        "DUY NHẤT (1 người HOẶC 1 vật HOẶC 1 nhóm cùng loại). TUYỆT ĐỐI CẤM tả '2 người cùng khung / đối đầu / "
        "chỉ tay nhau' QUÁ 1 LẦN cả beat. Lời nói về CẢ HAI người → TÁCH RA: shot này CHỈ người A (động tác "
        "riêng của A), shot kia CHỈ người B. Xen vật/cúp/số/đám đông/countryball/meme. Mỗi hint KHÁC HẲN nhau "
        "(KHÔNG na ná). Vẽ NGƯỜI là caricature NGƯỜI (đừng vẽ con dê/con vật trừ khi hint nói rõ mascot).\n"
        f"Sinh ~{n_target} shot (mỗi đoạn 1-2 shot, ~2-3s/shot). 'duration_weight' = trọng số tương đối "
        f"(KHÔNG phải giây). Người dẫn ~40% shot, xen B-roll thuần.\n\n"
        "Trả DUY NHẤT 1 JSON: {\"plan\":\"ý đồ ngắn\",\"shots\":[{\n"
        '  "seg":<int đoạn>, "transition_in":"cut|fade|glitch", "duration_weight":<0.5-2.0>,\n'
        '  "layout":"presenter_hero|presenter_corner|object_center|fullbleed_scene|icon_grid|terminal_fullbleed|side_by_side",\n'
        '  "content":{"kind":"real_photo|logo|screenshot|map|diagram|meme|doodle|terminal|countryball",'
        '"query":"CỤM TIẾNG ANH NGẮN mô tả hình để VẼ/tìm (LUÔN điền cho doodle/meme/object — máy vẽ chỉ hiểu '
        'tiếng Anh; vd \'gold trophy\', \'laughing meme face\', \'soccer ball\')","entity":"tên riêng người/đội","hint":"khoảnh khắc minh hoạ (tiếng Việt)"},\n'
        '  "content_motion":"slide_in_left|slide_in_right|pop_in|zoom_in|zoom_out|static|shake",\n'
        '  "presenter": null | {"role":"subject|reaction|accent","side":"left|right|center","motion":"static|rise_in|pop_in","pose_hint":"point|celebrate|shock|laugh|think|explain|smug|worry (theo HÀNH ĐỘNG shot)"},\n'
        '  "text": null | {"label":"CHỮ TO ≤24 ký tự"}\n'
        "}]}\n\n" + _FEWSHOT
    )


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
    return data if isinstance(data, dict) and isinstance(data.get("shots"), list) else None


def _coerce(val, valid: set, default: str) -> str:
    v = str(val or "").strip().lower()
    return v if v in valid else default


def _coerce_shot(raw: dict, n_seg: int) -> ShotSpec:
    """COERCE 1 shot dict → ShotSpec hợp lệ (enum sai → default, KHÔNG vứt cả shot)."""
    c = raw.get("content") or {}
    kind = _coerce(c.get("kind"), VALID_CONTENT_KINDS, "doodle")
    # real_photo/logo thiếu entity+query → hạ về doodle (resolver khỏi dead-end)
    if kind in ("real_photo", "logo") and not (str(c.get("entity") or "").strip() or str(c.get("query") or "").strip()):
        kind = "doodle"
    content = {"kind": kind, "query": str(c.get("query") or "")[:80],
               "entity": str(c.get("entity") or "")[:60], "hint": str(c.get("hint") or "")[:120]}
    pres = raw.get("presenter")
    if isinstance(pres, dict):
        ph = str(pres.get("pose_hint") or "").strip().lower()
        pres = {"role": _coerce(pres.get("role"), VALID_ROLES, "reaction"),
                "side": _coerce(pres.get("side"), VALID_SIDES, "right"),
                "motion": _coerce(pres.get("motion"), VALID_PRESENTER_MOTION, "static"),
                "pose_hint": ph if ph in VALID_POSE_HINTS else None}   # 6.1: gợi ý hành động pose
    else:
        pres = None
    txt = raw.get("text")
    txt = {"label": str(txt.get("label") or "")[:24]} if isinstance(txt, dict) and txt.get("label") else None
    try:
        seg = int(raw.get("seg", 0))
    except (TypeError, ValueError):
        seg = 0
    seg = min(max(seg, 0), max(0, n_seg - 1))
    try:
        w = float(raw.get("duration_weight", 1.0))
    except (TypeError, ValueError):
        w = 1.0
    # LAYOUT: coerce; sai/thiếu → default SUY TỪ content+presenter (terminal→terminal; glitch→glitch;
    # không người dẫn→object_center; có người dẫn→presenter_corner).
    if kind == "terminal":
        dft = "terminal_fullbleed"
    elif pres is None:
        dft = "object_center"
    else:
        dft = "presenter_corner"
    layout = _coerce(raw.get("layout"), VALID_LAYOUTS, dft)
    return ShotSpec(seg=seg, transition_in=_coerce(raw.get("transition_in"), VALID_TRANSITIONS, "cut"),
                    duration_weight=min(max(w, 0.5), 2.0), layout=layout, content=content,
                    content_motion=_coerce(raw.get("content_motion"), VALID_CONTENT_MOTION, "static"),
                    presenter=pres, text=txt)


def validate_and_repair(shots_raw: list, segments: list, n_target: int) -> list[ShotSpec]:
    """COERCE từng shot + sửa cấp-chuỗi (mọi đoạn ≥1 shot, ≤1 text/shot, người dẫn không liên tục, glitch ≤20%).
    Trả [] nếu số shot vô lý (ngoài [ceil(target/2), target*2]) → caller fallback cả beat."""
    n_seg = len(segments)
    specs = [_coerce_shot(s, n_seg) for s in shots_raw if isinstance(s, dict)]
    if not specs:
        return []
    # số shot vô lý → bỏ, fallback
    if not (max(1, n_target // 2) <= len(specs) <= n_target * 2 + 2):
        logger.warning(f"[planner] số shot {len(specs)} ngoài dải (target {n_target}) → fallback")
        return []
    # mọi đoạn phải có ≥1 shot (đoạn trống → chèn 1 shot doodle mặc định cho đoạn đó)
    covered = {s.seg for s in specs}
    for i in range(n_seg):
        if i not in covered:
            specs.append(ShotSpec(seg=i, content={"kind": "doodle", "query": "", "entity": "", "hint": ""}))
    specs.sort(key=lambda s: s.seg)
    # người dẫn KHÔNG phủ >2 shot liên tiếp → ép null ở giữa
    run = 0
    for s in specs:
        if s.presenter is not None:
            run += 1
            if run >= 3:
                s.presenter = None
                run = 0
        else:
            run = 0
    # glitch ≤20% → hạ phần dư về cut (giữ glitch đầu tiên)
    gl = [s for s in specs if s.transition_in == "glitch"]
    cap = max(1, int(len(specs) * _GLITCH_CAP))
    for s in gl[cap:]:
        s.transition_in = "cut"
    # CHỐNG ĐƠN ĐIỆU: >2 shot liền cùng layout → ép shot thứ 3 sang layout khác hợp content (founder báo).
    run = 1
    for i in range(1, len(specs)):
        if specs[i].layout == specs[i - 1].layout:
            run += 1
            if run >= 3:
                k = specs[i].content.get("kind")
                alt = ("object_center" if specs[i].layout != "object_center" and specs[i].presenter is None
                       else "presenter_corner" if specs[i].presenter else "fullbleed_scene")
                if k == "terminal":
                    alt = specs[i].layout       # giữ (terminal_fullbleed hợp lý)
                specs[i].layout = alt
                run = 1
        else:
            run = 1
    # CHỐNG "CHỈ 2 LAYOUT" (planner Groq yếu hay gom presenter_hero rỗng + object_center → người dẫn toàn
    # center-big y hệt, founder báo 'bố trí sai'): biến ~NỬA object_center (content trơ) → presenter_corner
    # (thêm người dẫn nhỏ-góc PHẢN ỨNG, luân phiên trái/phải) = chất kênh + đa dạng vị trí người dẫn.
    oc = [s for s in specs if s.layout == "object_center" and s.presenter is None
          and s.content.get("kind") not in ("terminal",)]
    for j, s in enumerate(oc):
        if j % 2 == 0:
            s.layout = "presenter_corner"
            s.presenter = {"role": "reaction", "side": ("right" if (j // 2) % 2 == 0 else "left"),
                           "motion": "static", "pose_hint": None}
    return specs


def _generate(beat, segments: list, n_target: int, *, feedback: str = "") -> list[ShotSpec]:
    """1 lượt: dựng prompt (+feedback nếu regen) → gọi LLM → parse → validate_and_repair. [] nếu hỏng."""
    from module2_brain.llm.v5_clients import complete_with_fallback

    user = _user_prompt(beat, segments, n_target)
    if feedback:
        user += f"\n\n⚠️ SỬA THEO GÓP Ý ĐẠO DIỄN (giữ đúng menu, đừng lặp lỗi):\n{feedback.strip()}\n"
    try:
        raw = complete_with_fallback(_SYSTEM, user, gemini_model=settings.gemini_model)
    except Exception as exc:  # noqa: BLE001 — LLM chết → []
        logger.warning(f"[planner] LLM lỗi: {str(exc)[:160]}")
        return []
    data = _parse(raw)
    if data is None:
        logger.warning("[planner] output không phải JSON shots dùng được")
        return []
    return validate_and_repair(data.get("shots") or [], segments, n_target)


def plan_beat_shots(beat, blocks, duration: float, *, visual_mode: str = "vuive_layered") -> list[ShotSpec]:
    """beat + blocks + duration → list[ShotSpec] (đã validate). [] → caller dựng fallback look cũ.

    Vòng: generate → CRITIC chấm → nếu < ngưỡng regen ĐÚNG 1 lần với feedback → lấy bản điểm cao hơn.
    """
    from video_engine.long_narrative.visual import _plan_segments

    segments = _plan_segments(duration, blocks)
    n_target = sum(max(1, round(sd / _SEC_PER_SHOT)) for _st, sd, _bi in segments)
    specs = _generate(beat, segments, n_target)
    if not specs:
        return []
    # CRITIC (fail-soft: critic lỗi → giữ bản hiện tại)
    try:
        from video_engine.long_narrative.shot_critic import score_plan
        score, fb = score_plan(specs, beat)
        if score < _CRITIC_THRESHOLD and fb:
            specs2 = _generate(beat, segments, n_target, feedback=fb)
            if specs2:
                score2, _ = score_plan(specs2, beat)
                if score2 > score:
                    logger.info(f"[planner] critic regen {score:.1f}→{score2:.1f} (nhận bản mới)")
                    specs = specs2
    except Exception as exc:  # noqa: BLE001 — critic không được làm hỏng plan
        logger.warning(f"[planner] critic lỗi (bỏ qua): {str(exc)[:120]}")
    logger.info(f"[planner] beat {getattr(beat, 'beat_id', '?')}: {len(specs)} shot ({len(segments)} đoạn)")
    return specs
