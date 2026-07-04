from src.video.validator import validate_video
from src.video.audio import extract_audio
from src.video.frames import extract_frames

from src.ai.transcriber import transcribe_audio
from src.ai.temporal_alignment import (
    build_temporal_windows,
)


VIDEO_PATH = "data/videos/test.mp4"
AUDIO_PATH = "data/audio/test.wav"
FRAME_DIR = "data/frames/test"


def main():
    print("1. Validating video...")

    metadata = validate_video(VIDEO_PATH)

    print("Video accepted:")
    print(metadata)

    print("\n2. Extracting audio...")

    audio_path = extract_audio(
        VIDEO_PATH,
        AUDIO_PATH,
    )

    print(
        f"Audio saved to: {audio_path}"
    )

    print("\n3. Extracting frames...")

    frames = extract_frames(
        VIDEO_PATH,
        FRAME_DIR,
        interval_seconds=5,
    )

    print(
        f"Extracted {len(frames)} frames."
    )

    print("\n4. Transcribing audio...")

    transcription = transcribe_audio(
        audio_path
    )

    print("\nTRANSCRIPT:\n")

    print(transcription["text"])

    print("\nTIMESTAMPED TRANSCRIPT:\n")

    for segment in transcription["segments"]:
        print(
            f"{segment['start']:>6.2f}s "
            f"- "
            f"{segment['end']:>6.2f}s "
            f"| {segment['text']}"
        )
        print("\n5. Building temporal windows...")

    windows = build_temporal_windows(
        frames=frames,
        transcript_segments=transcription["segments"],
        video_duration=metadata["duration"],
    )

    print("\nTEMPORAL WINDOWS:\n")

    for window in windows:
        print(
            f"{window['start_time']:.1f}s "
            f"- "
            f"{window['end_time']:.1f}s"
        )

        print(
            f"Frame: {window['frame_path']}"
        )

        if window["spoken_text"]:
            print(
                f"Speech: {window['spoken_text']}"
            )
        else:
            print("Speech: [NO SPEECH]")

        print()
    
    '''
    print(
        "\n5. Analysing visual timeline..."
    )

    visual_analysis = (
        analyse_visual_timeline(frames)
    )

    print("\nVISUAL SUMMARY:\n")

    print(
        visual_analysis.visual_summary
    )

    print("\nSETTING:\n")

    print(
        visual_analysis.setting
    )

    print("\nVISUAL STYLE:\n")

    print(
        visual_analysis.visual_style
    )

    print("\nVISUAL EVENTS:\n")

    for event in visual_analysis.events:
        print(
            f"{event.start_time:.1f}s "
            f"- "
            f"{event.end_time:.1f}s"
        )

        print(
            f"  {event.description}"
        )

        if event.visible_text:
            print(
                "  Visible text: "
                + ", ".join(
                    event.visible_text
                )
            )

        if event.entities:
            print(
                "  Entities: "
                + ", ".join(
                    event.entities
                )
            )

        print()

    print("\nVISUAL TONE:\n")

    print(
        visual_analysis.visual_tone
    )
    '''


if __name__ == "__main__":
    main()