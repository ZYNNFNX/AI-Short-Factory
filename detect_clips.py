import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
TRANSCRIPT_JSON = PROJECT_DIR / "data" / "transcripts" / "transcript.json"
CLIPS_DIR = PROJECT_DIR / "data" / "clips"
CLIP_CANDIDATES_JSON = CLIPS_DIR / "clip_candidates.json"
CLIP_CANDIDATES_TEXT = CLIPS_DIR / "clip_candidates.txt"

MIN_CLIP_SECONDS = 15
MAX_CLIP_SECONDS = 45
TOP_CLIP_COUNT = 5

HOOK_WORDS = [
    "how",
    "why",
    "best",
    "important",
    "secret",
    "mistake",
    "never",
    "always",
    "routine",
    "start",
]


def load_transcript():
    if not TRANSCRIPT_JSON.exists():
        raise FileNotFoundError(
            "No transcript found. Run 'python transcribe.py' first."
        )

    with TRANSCRIPT_JSON.open("r", encoding="utf-8") as file:
        return json.load(file)


def score_clip(text, duration):
    score = 0
    lower_text = text.lower()

    for word in HOOK_WORDS:
        if word in lower_text:
            score += 2

    if "?" in text:
        score += 3

    if MIN_CLIP_SECONDS <= duration <= MAX_CLIP_SECONDS:
        score += 5

    word_count = len(text.split())
    if word_count >= 25:
        score += 2

    return score


def build_clip_candidates(segments):
    candidates = []

    for start_index in range(len(segments)):
        clip_segments = []
        clip_start = segments[start_index]["start"]
        clip_end = clip_start

        for segment in segments[start_index:]:
            clip_segments.append(segment)
            clip_end = segment["end"]
            duration = clip_end - clip_start

            if duration < MIN_CLIP_SECONDS:
                continue

            if duration > MAX_CLIP_SECONDS:
                break

            clip_text = " ".join(item["text"] for item in clip_segments)
            score = score_clip(clip_text, duration)

            candidates.append(
                {
                    "start": round(clip_start, 2),
                    "end": round(clip_end, 2),
                    "duration": round(duration, 2),
                    "score": score,
                    "text": clip_text,
                }
            )

    candidates.sort(key=lambda clip: clip["score"], reverse=True)
    return candidates[:TOP_CLIP_COUNT]


def save_clip_candidates(candidates):
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    with CLIP_CANDIDATES_JSON.open("w", encoding="utf-8") as file:
        json.dump(candidates, file, indent=2, ensure_ascii=False)

    with CLIP_CANDIDATES_TEXT.open("w", encoding="utf-8") as file:
        for index, clip in enumerate(candidates, start=1):
            file.write(f"Clip {index}\n")
            file.write(f"Time: {clip['start']}s -> {clip['end']}s\n")
            file.write(f"Duration: {clip['duration']}s\n")
            file.write(f"Score: {clip['score']}\n")
            file.write(f"Text: {clip['text']}\n\n")

    print(f"Saved clip candidates JSON: {CLIP_CANDIDATES_JSON}")
    print(f"Saved readable clip candidates: {CLIP_CANDIDATES_TEXT}")


if __name__ == "__main__":
    transcript = load_transcript()
    clip_candidates = build_clip_candidates(transcript["segments"])
    save_clip_candidates(clip_candidates)
