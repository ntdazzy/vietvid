"""Router media — phục vụ video qua URL CÓ CHỮ KÝ (không cần Bearer → <video src> phát được).

Token cấp bởi GET /v1/jobs/{id}/video-url (authed). Endpoint này public nhưng chỉ chấp nhận
token HMAC hợp lệ (gắn job_id + org_id + hạn).
"""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select

from app_api.db import tenant_session
from app_api.media import verify_media_token
from app_api.models import Video

router = APIRouter(prefix="/v1/media", tags=["media"])


@router.get("/video/{job_id}")
def serve_video(job_id: uuid.UUID, token: str = Query(...)):
    org_id = verify_media_token(str(job_id), token)
    if org_id is None:
        raise HTTPException(status_code=403, detail="Token không hợp lệ hoặc đã hết hạn")
    with tenant_session(org_id) as s:
        v = s.execute(
            select(Video).where(Video.job_id == job_id, Video.org_id == org_id)
        ).scalar_one_or_none()
        url = v.storage_url if v else None
    if not url:
        raise HTTPException(status_code=404, detail="Chưa có video")
    if url.startswith(("http://", "https://")):
        return RedirectResponse(url)
    if not os.path.exists(url):
        raise HTTPException(status_code=404, detail="file_missing")
    return FileResponse(url, media_type="video/mp4", filename=f"{job_id}.mp4")
