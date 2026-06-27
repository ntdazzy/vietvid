"""Quét claim cấm (luật quảng cáo VN) — scanner thuần + endpoint vận hành thật."""

from __future__ import annotations

from app_api import claims


def test_blocks_medical_cure_claim():
    f = claims.scan_claims("Sản phẩm chữa khỏi mụn 100% sau 3 ngày.")
    assert claims.has_blocking(f)
    assert any("chữa" in x["match"].lower() for x in f)


def test_blocks_financial_guarantee():
    f = claims.scan_claims("Đầu tư cam kết lãi 20% mỗi tháng.")
    assert claims.has_blocking(f)


def test_warns_absolute_superlative():
    f = claims.scan_claims("Đây là sản phẩm tốt nhất Việt Nam.")
    assert f and not claims.has_blocking(f)  # 'tốt nhất' chỉ cảnh báo, không chặn
    assert f[0]["severity"] == "warn"


def test_clean_text_no_findings():
    assert claims.scan_claims("Tai nghe pin trâu, chống ồn, giá tốt.") == []


def test_dedupes_repeated_claims():
    f = claims.scan_claims("chữa khỏi ... chữa khỏi ... chữa khỏi")
    assert len([x for x in f if "chữa" in x["match"].lower()]) == 1


def test_scan_script_tags_beat_index():
    script = {"beats": [
        {"narration": "Mua ngay nha."},
        {"narration": "Giảm 10kg thần tốc luôn."},
    ]}
    f = claims.scan_script(script)
    assert any(x["beat_index"] == 1 for x in f)


def test_check_claims_endpoint(client, user):
    r = client.post("/v1/script/check-claims", headers=user["headers"],
                    json={"text": "Thuốc này điều trị tận gốc bệnh."})
    assert r.status_code == 200
    assert r.json()["has_blocking"] is True


def test_generate_includes_claim_warnings(client, user):
    # kịch bản template mặc định KHÔNG dính claim cấm → mảng rỗng nhưng key có mặt
    d = client.post("/v1/script/generate", headers=user["headers"],
                    json={"product": {"name": "Bình nước"}, "seconds": 12}).json()
    assert "claim_warnings" in d
