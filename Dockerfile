# VietVid app_api (FastAPI + engine) — container cho Render/Fly/Railway.
# Web (Next.js) deploy riêng lên Vercel; container này CHỈ là backend + worker (inline).
FROM python:3.12-slim

# ffmpeg (compose/render) + libs cho opencv/onnx (scenedetect/rembg trong engine)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg ca-certificates libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# chỉ copy phần backend cần (apps/ web không vào container này — xem .dockerignore)
COPY app_api ./app_api
COPY video_engine ./video_engine
COPY core ./core
COPY config ./config
COPY module2_brain ./module2_brain
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 VIETVID_ENV=production
EXPOSE 8000

# migrate (idempotent) rồi chạy API. PORT do nền tảng (Render/Fly) cấp.
CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
