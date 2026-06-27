"""Bộ máy sinh kịch bản — engine thuần (không key) + endpoint vận hành thật."""

from __future__ import annotations

from app_api import scriptgen

_PRODUCT = {"name": "Tai nghe ABC Pro", "category": "tai nghe", "price": "199.000đ"}


def test_engine_structure_all_angles():
    for angle in scriptgen.ANGLE_LABELS:
        s = scriptgen.generate_script(product=_PRODUCT, angle=angle, seconds=15)
        assert s["angle"] == angle
        assert s["beats"], "phải có beats"
        assert s["beats"][0]["label"] == "hook"
        assert s["beats"][-1]["label"] == "cta"
        # timecode liền mạch, beat cuối khớp tổng thời lượng
        assert s["beats"][0]["t_start"] == 0
        assert s["beats"][-1]["t_end"] == 15
        # sản phẩm đã được nhúng vào lời thoại
        assert "ABC Pro" in s["narration_full"]
        assert "199.000đ" in s["narration_full"]


def test_engine_beat_count_scales_with_duration():
    assert len(scriptgen.generate_script(product=_PRODUCT, seconds=9)["beats"]) == 3
    assert len(scriptgen.generate_script(product=_PRODUCT, seconds=30)["beats"]) == 5


def test_engine_missing_price_graceful():
    s = scriptgen.generate_script(product={"name": "Áo thun"}, seconds=12)
    assert "giá tốt" in s["narration_full"]  # fallback giá
    assert "Áo thun" in s["narration_full"]


def test_apply_strategist_overrides_beats():
    base = scriptgen.generate_script(product=_PRODUCT, seconds=15)
    brief = {
        "angle": "transformation",
        "hook_line": "Lên đời trong 3 giây!",
        "beats": [
            {"label": "hook", "says": "Coi nè, khác hẳn luôn", "shows": "khoe sp"},
            {"label": "cta", "says": "Chốt đơn ngay", "shows": "chỉ giỏ"},
        ],
        "cta_plan": "Bấm giỏ hàng kẻo hết!",
    }
    out = scriptgen.apply_strategist(base, brief)
    assert out["hook_line"] == "Lên đời trong 3 giây!"
    assert out["angle"] == "transformation"
    assert len(out["beats"]) == 2
    assert out["beats"][-1]["t_end"] == 15  # timecode phân bổ lại
    assert out["cta"] == "Bấm giỏ hàng kẻo hết!"
    assert out["source"] == "strategist+template"


def test_captions_cover_full_duration_monotonic():
    s = scriptgen.generate_script(product=_PRODUCT, seconds=15)
    cues = scriptgen.build_captions(s)
    assert cues, "phải có cue"
    assert cues[0]["start"] == 0
    assert cues[-1]["end"] == 15  # phủ kín tới hết
    # timing đơn điệu tăng, không chồng lấn
    for a, b in zip(cues, cues[1:]):
        assert a["end"] <= b["start"] + 0.01
        assert a["start"] <= a["end"]


def test_srt_format_valid():
    s = scriptgen.generate_script(product=_PRODUCT, seconds=12)
    srt = scriptgen.to_srt(scriptgen.build_captions(s))
    assert "-->" in srt and "00:00:00,000" in srt
    assert srt.split("\n", 1)[0] == "1"  # block đầu đánh số 1


def test_vtt_has_header():
    s = scriptgen.generate_script(product=_PRODUCT, seconds=8)
    vtt = scriptgen.to_vtt(scriptgen.build_captions(s))
    assert vtt.startswith("WEBVTT")
    assert "." in vtt.split("-->")[0]  # VTT dùng dấu chấm cho ms


def test_long_narration_splits_into_multiple_cues():
    beat = {"t_start": 0, "t_end": 10,
            "narration": "Một hai ba bốn năm sáu bảy tám chín mười, mười một mười hai mười ba."}
    cues = scriptgen.build_captions({"beats": [beat]})
    assert len(cues) >= 2  # câu dài bị tách
    assert cues[-1]["end"] == 10


# ── endpoint (vận hành thật qua uvicorn subprocess) ──────────────────────────
def test_script_endpoint_requires_auth(client):
    r = client.post("/v1/script/generate", json={"product": {"name": "X"}})
    assert r.status_code in (401, 403)


def test_script_endpoint_generates(client, user):
    r = client.post("/v1/script/generate", headers=user["headers"], json={
        "product": {"name": "Bình giữ nhiệt Q", "category": "đồ gia dụng", "price": "250.000đ"},
        "angle": "fomo_scarcity", "seconds": 15, "voice_gender": "male",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["angle"] == "fomo_scarcity"
    assert d["voice_gender"] == "male"
    assert "Bình giữ nhiệt Q" in d["narration_full"]
    assert len(d["beats"]) >= 3


def test_script_angles_list(client, user):
    rows = client.get("/v1/script/angles", headers=user["headers"]).json()
    assert any(a["value"] == "social_proof" for a in rows)


def test_generate_includes_cues(client, user):
    d = client.post("/v1/script/generate", headers=user["headers"], json={
        "product": {"name": "Nồi chiên không dầu"}, "seconds": 15,
    }).json()
    assert d["cues"] and d["cues"][0]["start"] == 0


def test_captions_endpoint_srt(client, user):
    beats = [{"t_start": 0, "t_end": 6, "narration": "Sản phẩm này đỉnh thật sự nha mọi người."}]
    r = client.post("/v1/script/captions", headers=user["headers"], json={"beats": beats, "fmt": "srt"})
    assert r.status_code == 200
    d = r.json()
    assert d["format"] == "srt" and "-->" in d["content"]
    assert d["cues"][-1]["end"] == 6
