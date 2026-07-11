import os

from faster_whisper import WhisperModel


# "small" (~244M params) OOM-killed the Railway deployment; "base" (~74M)
# reduced but did not eliminate it — confirmed intermittent even on "base"
# (bare "Killed" in the container logs — a SIGKILL from the OOM killer,
# not a Python exception), meaning the deployment is operating right at
# its memory ceiling and any model size is a mitigation, not a guarantee.
# "tiny" (~39M params) is the smallest available. Override via
# WHISPER_MODEL_SIZE on a host with more memory headroom, where transcript
# accuracy matters more than staying under a tight limit.
DEFAULT_WHISPER_MODEL_SIZE = "tiny"

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