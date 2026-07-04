from faster_whisper import WhisperModel


_model = None


def get_transcription_model() -> WhisperModel:
    global _model

    if _model is None:
        print("Loading transcription model...")

        _model = WhisperModel(
            "small",
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