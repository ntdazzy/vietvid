"""Share công khai — share-url (TTL dài) trỏ /share/{id}/{token}; video phát KHÔNG cần auth."""

from __future__ import annotations

import os
import tempfile
import uuid

import httpx
from sqlalchemy import text

from app_api import jobs as jobs_svc
from app_api.db import tenant_session
from app_api.models import Video
from tests.conftest import JOB_SPEC


def test_share_url_public_playback(client, user, server):
    # tạo job READY + Video row trỏ file mp4 giả
    mp4 = os.path.join(tempfile.gettempdir(), f"vv_share_{uuid.uuid4().hex[:6]}.mp4")
    open(mp4, "wb").write(b"\x00\x00\x00\x18ftypmp42SHAREBYTES" * 40)
    with tenant_session(user["org_id"]) as s:
        job, _, _ = jobs_svc.create_job(
            s, uuid.UUID(user["org_id"]), uuid.UUID(user["uid"]),
            idempotency_key=f"k-{uuid.uuid4().hex[:10]}", spec_input=JOB_SPEC,
        )
        jid = job.id
        s.execute(text("UPDATE jobs SET status='READY' WHERE id=:id"), {"id": jid})
        s.add(Video(org_id=uuid.UUID(user["org_id"]), job_id=jid, storage_url=mp4,
                    has_watermark=False, aspect="9:16"))

    r = client.get(f"/v1/jobs/{jid}/share-url", headers=user["headers"])
    assert r.status_code == 200
    assert f"/share/{jid}/" in r.json()["share_url"]
    video_path = r.json()["video_url"]

    # phát công khai (KHÔNG Bearer)
    raw = httpx.Client(base_url=server, follow_redirects=False, timeout=30)
    resp = raw.get(video_path)
    assert resp.status_code == 200 and len(resp.content) > 300

    # dọn
    with tenant_session(user["org_id"]) as s:
        s.execute(text("DELETE FROM videos WHERE job_id=:id"), {"id": jid})
        jobs_svc.release_hold(s, uuid.UUID(user["org_id"]), jid, note="cleanup")
    try:
        os.remove(mp4)
    except OSError:
        pass
