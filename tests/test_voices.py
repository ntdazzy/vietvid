"""Thư viện giọng persona — resolver thuần + endpoint danh mục (vận hành thật)."""

from __future__ import annotations

from app_api import voices


def test_resolve_known_persona():
    voice, rate, pitch = voices.resolve("mai")
    assert voice == "vi-VN-HoaiMyNeural"  # Mai là nữ
    assert rate == "+8%" and pitch == "+2Hz"


def test_resolve_male_persona():
    voice, _, _ = voices.resolve("hung")
    assert voice == "vi-VN-NamMinhNeural"  # Hùng là nam


def test_resolve_unknown_falls_back_to_gender():
    voice, rate, pitch = voices.resolve("khong-co", gender="male")
    assert voice == "vi-VN-NamMinhNeural"
    assert rate == "+0%" and pitch == "+0Hz"


def test_every_persona_resolves_to_valid_edge_format():
    for p in voices.VOICE_PERSONAS:
        voice, rate, pitch = voices.resolve(p["id"])
        assert voice.startswith("vi-VN-")
        assert rate.endswith("%") and pitch.endswith("Hz")


def test_personas_endpoint(client, user):
    rows = client.get("/v1/voice/personas", headers=user["headers"]).json()
    ids = {p["id"] for p in rows}
    assert {"mai", "khoa", "linh", "hung"} <= ids
    assert all("vibe" in p and "blurb" in p for p in rows)


def test_personas_endpoint_requires_auth(client):
    assert client.get("/v1/voice/personas").status_code in (401, 403)
