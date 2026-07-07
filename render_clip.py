import json
import shutil
import subprocess
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "data" / "source"
CLIP_CANDIDATES_JSON = PROJECT_DIR / "data" / "clips" / "clip_candidates.json"
FINAL_CLIPS_DIR = PROJECT_DIR / "data" / "final_clips"
OUTPUT_CLIP = FINAL_CLIPS_DIR / "clip_1.mp4"


def find_ffmpeg():
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path is None:
        raise FileNotFoundError(
            "ffmpeg was not found. Close VS Code, reopen it, then run "
            "'ffmpeg -version' in the terminal."
        )

    return ffmpeg_path


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


def load_best_clip_candidate():
    if not CLIP_CANDIDATES_JSON.exists():
        raise FileNotFoundError(
            "No clip candidates found. Run 'python detect_clips.py' first."
        )

    with CLIP_CANDIDATES_JSON.open("r", encoding="utf-8") as file:
        candidates = json.load(file)

    if not candidates:
        raise ValueError("clip_candidates.json is empty.")

    return candidates[0]


def render_clip(ffmpeg_path, source_video, clip_candidate):
    FINAL_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    start_time = str(clip_candidate["start"])
    duration = str(clip_candidate["duration"])

    command = [
        ffmpeg_path,
        "-y",
        "-ss",
        start_time,
        "-i",
        str(source_video),
        "-t",
        duration,
        "-c",
        "copy",
        str(OUTPUT_CLIP),
    ]

    print("Rendering first clip candidate...")
    print(f"Start: {start_time}s")
    print(f"Duration: {duration}s")

    subprocess.run(command, check=True)

    print(f"Saved final clip: {OUTPUT_CLIP}")


if __name__ == "__main__":
    ffmpeg = find_ffmpeg()
    source = find_source_video()
    best_clip = load_best_clip_candidate()
    render_clip(ffmpeg, source, best_clip)
