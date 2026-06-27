"""Storage — local fallback (chưa cấu hình cloud) + dọn workdir đúng (giữ final, xoá dư)."""

from __future__ import annotations

import os
import uuid

from app_api import storage


def _mk_workdir(job_id) -> str:
    wd = storage._workdir(job_id)
    os.makedirs(wd, exist_ok=True)
    for name in ("final.mp4", "clip.mp4", "image_1.png", "voice.wav"):
        with open(os.path.join(wd, name), "wb") as f:
            f.write(b"x" * 100)
    return wd


def test_store_output_local_when_unconfigured(tmp_path):
    # chưa cấu hình S3 → trả nguyên local path
    p = tmp_path / "final.mp4"
    p.write_bytes(b"video")
    assert storage.store_output(str(p), uuid.uuid4()) == str(p)


def test_cleanup_keeps_final_deletes_intermediates():
    jid = uuid.uuid4()
    wd = _mk_workdir(jid)
    final = os.path.join(wd, "final.mp4")
    storage.cleanup_workdir(jid, keep=final)
    remaining = set(os.listdir(wd))
    assert remaining == {"final.mp4"}  # giữ final, xoá clip/image/voice
    # dọn nốt cả thư mục
    storage.cleanup_workdir(jid, keep=None)
    assert not os.path.isdir(wd)


def test_cleanup_none_removes_whole_dir():
    jid = uuid.uuid4()
    wd = _mk_workdir(jid)
    storage.cleanup_workdir(jid, keep=None)
    assert not os.path.isdir(wd)


def test_sweep_noop_when_unconfigured():
    # local-mode → KHÔNG quét xoá (final.mp4 đang serve) → trả 0
    assert storage.sweep_old_workdirs() == 0
