"""Affiliate loop — short-link /r/{code} redirect + ghi click + stats + cô lập org."""

from __future__ import annotations

import httpx


def test_create_link_and_redirect_tracks_click(client, user, server):
    r = client.post("/v1/affiliate/links", headers=user["headers"],
                    json={"target_url": "https://shopee.vn/product/123", "label": "SP A", "network": "shopee"})
    assert r.status_code == 201
    code = r.json()["code"]
    assert f"/r/{code}" in r.json()["short_url"]

    # redirect public (KHÔNG auth) → 302 tới target
    raw = httpx.Client(base_url=server, follow_redirects=False, timeout=30)
    resp = raw.get(f"/r/{code}")
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://shopee.vn/product/123"
    # click thứ 2
    raw.get(f"/r/{code}")

    # stats phản ánh click
    st = client.get("/v1/affiliate/stats", headers=user["headers"]).json()
    assert st["links"] >= 1 and st["clicks"] >= 2
    # list link có clicks
    links = client.get("/v1/affiliate/links", headers=user["headers"]).json()
    assert next(x for x in links if x["code"] == code)["clicks"] >= 2


def test_redirect_unknown_code_404(server):
    raw = httpx.Client(base_url=server, follow_redirects=False, timeout=30)
    assert raw.get("/r/khongtontai").status_code == 404


def test_links_isolated_between_orgs(client, user, user2):
    r = client.post("/v1/affiliate/links", headers=user["headers"],
                    json={"target_url": "https://lazada.vn/x"})
    lid = r.json()["id"]
    b_links = client.get("/v1/affiliate/links", headers=user2["headers"]).json()
    assert not any(x["id"] == lid for x in b_links)
    # B không xoá được link của A
    assert client.delete(f"/v1/affiliate/links/{lid}", headers=user2["headers"]).status_code == 404


def test_invalid_target_url_422(client, user):
    assert client.post("/v1/affiliate/links", headers=user["headers"],
                       json={"target_url": "javascript:alert(1)"}).status_code == 422
