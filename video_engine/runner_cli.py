"""M0 — chạy engine stateless từ CLI, KHÔNG cần DB.

    python -m video_engine.runner_cli <jobspec.json> [--workdir DIR]

Đọc JobSpec JSON → render(spec, NullSink) → in RenderResult (path, status, cost, timings).
Verify offline: đặt VIDEO_PROVIDER=mock + IMAGE_PROVIDER=mock trong .env để chạy không cần
API key/GPU (mock clip → ffmpeg compose → qa).
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv: list[str] | None = None) -> int:
    # Windows console mặc định cp1258 → vỡ khi in tiếng Việt (RenderResult.error). Ép UTF-8.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(prog="video_engine.runner_cli")
    ap.add_argument("jobspec", help="đường dẫn file JobSpec JSON")
    ap.add_argument("--workdir", default="", help="thư mục output (mặc định: tạm)")
    args = ap.parse_args(argv)

    from video_engine.render_service import render
    from video_engine.sink import NullSink
    from video_engine.spec import JobSpec

    with open(args.jobspec, encoding="utf-8") as f:
        data = json.load(f)
    if args.workdir:
        os.makedirs(args.workdir, exist_ok=True)
        data["workdir"] = args.workdir
    spec = JobSpec.from_dict(data)

    sink = NullSink()
    result = render(spec, sink)

    print("=" * 60)
    print(f"STATUS      : {result.status}")
    print(f"PATH        : {result.path}")
    print(f"COST_USD    : {result.cost_usd}")
    print(f"CLIPS_USED  : {result.clips_used}")
    print(f"FAULT_CLASS : {result.fault_class}")
    if result.error:
        print(f"ERROR       : {result.error}")
    print(f"TIMINGS     : {json.dumps(result.stage_timings, ensure_ascii=False)}")
    print("=" * 60)
    if result.path and os.path.exists(result.path):
        print(f"OK → video tại: {result.path} ({os.path.getsize(result.path)} bytes)")
        return 0
    return 1 if result.status not in ("READY",) else 0


if __name__ == "__main__":
    sys.exit(main())
