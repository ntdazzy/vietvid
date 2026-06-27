"""KOL mặc định — persona TEXT (không cần ảnh mặt), dùng cho video text-based.

``character_sheet`` (tiếng Anh) là đoạn Director nhúng vào video_prompt để Seedance
TỰ SINH nhân vật — học cấu trúc mô tả từ kho autovis (koc-context). KHÔNG gửi ảnh mặt.
"""

from __future__ import annotations

import json

from sqlalchemy import select

from core.database import db
from core.logger import logger
from core.models import KolCharacter, KolStatus

# 6 KOL hạt giống — đủ nam/nữ + đa ngành (thời trang/beauty/công nghệ/thể thao/gia dụng/F&B).
KOL_SEED: list[dict] = [
    {
        "name": "Linh Đan", "gender": "nữ", "style": "Thân thiện",
        "persona": "KOC nữ trẻ gần gũi, hợp beauty & thời trang nữ",
        "character_sheet": "A young East Asian woman, early 20s, long loose wavy black hair, fair skin, "
        "natural pink blush makeup, soft friendly smile, slim feminine build; casual chic outfit, "
        "warm approachable energy — speaks like a close friend recommending a product.",
        "tags": ["beauty", "thời trang", "chung"],
    },
    {
        "name": "Bảo Châu", "gender": "nữ", "style": "Sang trọng",
        "persona": "KOC nữ thanh lịch, hợp skincare cao cấp & mỹ phẩm",
        "character_sheet": "An elegant East Asian woman, mid 20s, smooth porcelain glass skin, oval face, "
        "delicate jawline, almond brown eyes, straight soft eyebrows, sleek hair; refined premium style, "
        "calm trustworthy tone — ideal for high-end skincare and cosmetics.",
        "tags": ["skincare", "beauty", "quà tặng"],
    },
    {
        "name": "Mỹ Linh", "gender": "nữ", "style": "Năng động",
        "persona": "KOC nữ Gen Z sôi nổi, hợp F&B & lifestyle TikTok",
        "character_sheet": "A lively Gen Z East Asian woman, around 20, fair skin, trendy streetwear, "
        "expressive playful face, dynamic body language; high-energy TikTok creator vibe — great for "
        "food, drinks and everyday lifestyle products.",
        "tags": ["F&B", "thực phẩm", "chung"],
    },
    {
        "name": "Minh Quân", "gender": "nam", "style": "Chuyên nghiệp",
        "persona": "KOC nam lịch lãm, hợp công nghệ & gia dụng",
        "character_sheet": "A handsome East Asian man, around 25, tall slim athletic build, very fair skin, "
        "short black side-swept hair, sharp sculpted jawline, deep-set dark brown eyes, confident calm gaze; "
        "smart-casual outfit, credible professional tone — ideal for tech and home appliances.",
        "tags": ["công nghệ", "gia dụng"],
    },
    {
        "name": "Hoàng Phúc", "gender": "nam", "style": "Thể thao",
        "persona": "KOC nam khỏe khoắn, hợp thể thao & gadget",
        "character_sheet": "A young East Asian male model, 20-25, tall athletic lean build with toned legs, "
        "natural fair skin, dark medium-length textured hair with side-swept fringe, energetic confident "
        "expression; sporty outfit — perfect for sports gear and active-lifestyle gadgets.",
        "tags": ["thể thao", "công nghệ"],
    },
    {
        "name": "Gia Bảo", "gender": "nam", "style": "Chất chơi",
        "persona": "KOC nam Gen Z street, hợp thời trang nam & phụ kiện",
        "character_sheet": "A young East Asian man in his early 20s, sharp jawline, fair skin, black "
        "textured side-swept Korean hairstyle, relaxed confident expression with a subtle smirk; trendy "
        "street fashion — great for menswear, accessories and youth brands.",
        "tags": ["thời trang", "chung"],
    },
    # Kênh "Tủ Đồ của Chin Và Chun" — cặp nhân vật AI mặt THUẦN VIỆT, tự nhiên (chống "AI quá").
    # character_sheet theo TAI-LIEU-GOC-KENH-CHIN-CHUN.md mục 18.1/18.2.
    {
        "name": "Chin", "gender": "nữ", "style": "Trẻ trung tự nhiên",
        "persona": "Nhân vật AI NỮ của kênh Tủ Đồ của Chin Và Chun — phụ nữ Việt trẻ TRƯỞNG THÀNH "
        "(~24 tuổi), gần gũi, thanh lịch, hợp thời trang trend Gen Z. Không lộ chất AI.",
        "character_sheet": "Photorealistic young ADULT Vietnamese woman, around 24 years old (clearly a "
        "grown adult, not a teenager), real girl-next-door look (NOT a fashion-model build): around "
        "1m55-1m58, slim but healthy with soft natural curves and a little extra softness, a feminine "
        "figure with some flesh — definitely NOT skinny, not supermodel proportions. Authentic "
        "Vietnamese face with soft slightly rounded cheeks, naturally fair and bright skin (a touch "
        "fairer) but REAL skin — visible fine pores, a few faint freckles on the cheeks and nose, "
        "natural skin texture, NOT airbrushed. Warm friendly half-smile, cute and approachable like a "
        "Vietnamese streamer, gentle bright eyes, natural dark-brown almost black eyebrows. Long "
        "straight black hair, slightly loose with a few natural flyaway strands. Candid amateur "
        "phone-photo realism, soft natural daylight. Absolutely NO plastic skin, NO over-smoothing, "
        "NO beauty-filter glow, NO porcelain doll look, NO exaggerated AI-perfect smile.",
        "tags": ["thời trang", "chin", "chin-chun", "chung"],
    },
    {
        "name": "Chun", "gender": "nam", "style": "Boy phố Việt",
        "persona": "Nhân vật AI NAM của kênh Tủ Đồ của Chin Và Chun — trai phố Việt ~26-27, có cá tính, "
        "streetwear, hợp đồ nam. Không lộ chất AI, không sao Hàn giả trân.",
        "character_sheet": "Photorealistic young Vietnamese man, 27 years old, authentic Vietnamese "
        "'city boy / boy pho' vibe with personality — stylish, streetwear-leaning, effortlessly cool. "
        "Around 1m72, slim and slightly lean build (lean, not skinny). Real Vietnamese man's face with "
        "natural medium skin tone, visible pores and authentic skin texture, light natural stubble, "
        "defined but soft jawline, expressive dark eyes, a genuinely nice natural smile. Black short-to-"
        "medium hair in a modern street cut, slightly messy and natural. Candid street-style photo "
        "realism. NOT a polished K-pop idol look, NO plastic skin, NO beauty filter, NO over-perfect "
        "AI male model face.",
        "tags": ["thời trang", "chun", "chin-chun", "chung"],
    },
]


def ensure_default_kols() -> None:
    """Seed KOL hạt giống (chỉ thêm khi thư viện còn ít — không ghi đè KOL founder tạo)."""
    with db.transaction() as session:
        existing = set(n.lower() for n in session.scalars(select(KolCharacter.name)).all())
        added = 0
        for spec in KOL_SEED:
            if spec["name"].lower() in existing:
                continue
            session.add(KolCharacter(
                name=spec["name"], gender=spec["gender"], style=spec["style"],
                persona=spec["persona"], character_sheet=spec["character_sheet"],
                tags=json.dumps(spec["tags"], ensure_ascii=False),
                image_source="generated", status=KolStatus.ACTIVE,
            ))
            added += 1
        if added:
            logger.info(f"[kols] seed {added} KOL hạt giống vào kol_characters")
