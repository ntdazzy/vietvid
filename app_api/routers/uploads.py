"""Upload ảnh nguồn (B1 wizard). MVP: lưu file local → trả image_path cho engine đọc.

Dev: app_api + worker cùng máy (inline executor) → local path dùng được ngay. Production
(worker cloud) sẽ thay bằng presigned R2 upload — cùng interface trả {image_path}.
"""

from __future__ import annotations

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app_api.deps import Tenant, get_tenant

router = APIRouter(prefix="/v1/uploads", tags=["uploads"])

UPLOAD_DIR = os.environ.get("VIETVID_UPLOAD_DIR") or os.path.join(
    tempfile.gettempdir(), "vietvid_uploads"
)
_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_BYTES = 12 * 1024 * 1024


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_tenant),
) -> dict:
    if file.content_type not in _EXT:
        raise HTTPException(415, "Chỉ nhận ảnh JPEG/PNG/WebP")
    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "Ảnh quá lớn (>12MB)")
    if not data:
        raise HTTPException(422, "File rỗng")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    name = f"{tenant.org_id}_{uuid.uuid4().hex}{_EXT[file.content_type]}"
    dest = os.path.join(UPLOAD_DIR, name)
    with open(dest, "wb") as f:
        f.write(data)
    return {"image_path": dest, "filename": file.filename or name, "bytes": len(data)}
