import json
from pathlib import Path

from faster_whisper import WhisperModel


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "data" / "source"
TRANSCRIPT_DIR = PROJECT_DIR / "data" / "transcripts"

TRANSCRIPT_JSON = TRANSCRIPT_DIR / "transcript.json"
TRANSCRIPT_TEXT = TRANSCRIPT_DIR / "transcript.txt"


def find_source_video():
    video_files = [
        path
        for path in SOURCE_DIR.glob("source_video.*")
        if path.suffix != ".json"
    ]

    if not video_files:
        raise FileNotFoundError(
            "No source video found. Run 'python ingest.py' first."
        )

    return video_files[0]


def transcribe_video(video_path):
    print("Loading Whisper transcription model...")
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    print(f"Transcribing video: {video_path}")
    segments, info = model.transcribe(str(video_path), beam_size=1)

    transcript_segments = []

    for segment in segments:
        transcript_segments.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            }
        )

    return {
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "segments": transcript_segments,
    }


def save_transcript(transcript):
    TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

    with TRANSCRIPT_JSON.open("w", encoding="utf-8") as json_file:
        json.dump(transcript, json_file, indent=2, ensure_ascii=False)

    with TRANSCRIPT_TEXT.open("w", encoding="utf-8") as text_file:
        for segment in transcript["segments"]:
            text_file.write(
                f"[{segment['start']}s -> {segment['end']}s] {segment['text']}\n"
            )

    print(f"Saved transcript JSON: {TRANSCRIPT_JSON}")
    print(f"Saved readable transcript: {TRANSCRIPT_TEXT}")


if __name__ == "__main__":
    source_video = find_source_video()
    transcript_data = transcribe_video(source_video)
    save_transcript(transcript_data)
