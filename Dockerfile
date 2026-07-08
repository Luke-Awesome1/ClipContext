# ClipContext backend — FastAPI + video/AI pipeline.
# Requires a persistent container host (not a short-lived serverless function):
# the pipeline shells out to ffmpeg, writes job artifacts to local disk, and
# runs long background jobs in-process.
FROM python:3.13-slim

# ffmpeg is required for audio extraction (src/video/audio.py) and video
# metadata probing (src/video/validator.py via ffprobe).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src ./src

# Runtime directories are also created lazily by src/pipeline/paths.py, but
# creating them at build time avoids a first-request race under concurrency.
RUN mkdir -p data/videos/uploads data/audio data/frames outputs

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Honor $PORT for hosts that assign it dynamically (Cloud Run, Railway, etc.)
# while defaulting to 8000 for plain `docker run`.
CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
