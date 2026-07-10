import os

from faster_whisper import WhisperModel


# "small" (~244M params) was OOM-killing the Railway deployment: combined
# with frame extraction buffers, ffmpeg, and the FastAPI process already
# resident in memory at this point in the pipeline, it pushed the
# container past its memory limit (confirmed via a bare "Killed" in the
# container logs — a SIGKILL from the OOM killer, not a Python exception).
# "base" (~74M params) cuts the model's memory footprint roughly 3x.
# Override via WHISPER_MODEL_SIZE if running on a host with more memory
# headroom and better transcription accuracy is worth the tradeoff.
DEFAULT_WHISPER_MODEL_SIZE = "base"

_model = None


def get_transcription_model() -> WhisperModel:
    global _model

    if _model is None:
        model_size = os.getenv("WHISPER_MODEL_SIZE", DEFAULT_WHISPER_MODEL_SIZE)

        print(f"Loading transcription model ({model_size})...")

        _model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )

    return _model


def transcribe_audio(audio_path: str) -> dict:
    model = get_transcription_model()

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
    )

    transcript_segments = []
    full_text_parts = []

    for segment in segments:
        text = segment.text.strip()

        if not text:
            continue

        transcript_segments.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": text,
            }
        )

        full_text_parts.append(text)

    full_text = " ".join(full_text_parts)

    return {
        "language": info.language,
        "language_probability": round(
            info.language_probability,
            4,
        ),
        "text": full_text,
        "segments": transcript_segments,
    }