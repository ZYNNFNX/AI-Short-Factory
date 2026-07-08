import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict
import tempfile

from caption_renderer import extract_word_timestamps
from utils import load_config, VideoProcessingError, setup_logging

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = PROJECT_DIR / "data" / "source"
CLIP_CANDIDATES_JSON = PROJECT_DIR / "data" / "clips" / "clip_candidates.json"
TRANSCRIPT_JSON = PROJECT_DIR / "data" / "transcripts" / "transcript.json"
FINAL_CLIPS_DIR = PROJECT_DIR / "data" / "final_clips"
OUTPUT_CLIP = FINAL_CLIPS_DIR / "clip_1.mp4"

# Load configuration
config = load_config()
OUTPUT_CONFIG = config.get("output", {})
CAPTION_CONFIG = config.get("captions", {})

OUTPUT_FPS = OUTPUT_CONFIG.get("frame_rate", 30)
OUTPUT_BITRATE = OUTPUT_CONFIG.get("bitrate", "8000k")
AUDIO_BITRATE = OUTPUT_CONFIG.get("audio_bitrate", "128k")
ENABLE_CAPTIONS = CAPTION_CONFIG.get("enable_captions", True)
# Face tracking / output framing config (used to force 9:16 output)
FACE_CONFIG = config.get("face_tracking", {})
TARGET_WIDTH = FACE_CONFIG.get("target_crop_width", 1080)
TARGET_HEIGHT = FACE_CONFIG.get("target_crop_height", 1920)


def find_ffmpeg() -> str:
    """Find ffmpeg executable in system PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    
    if ffmpeg_path is None:
        raise FileNotFoundError(
            "ffmpeg not found. Install ffmpeg or add it to PATH, then restart VS Code."
        )
    
    return ffmpeg_path


def find_source_video() -> Path:
    """Find source video file."""
    video_files = [
        path for path in SOURCE_DIR.glob("source_video.*")
        if path.suffix.lower() in [".mp4", ".avi", ".mkv", ".mov", ".webm"]
    ]
    
    if not video_files:
        raise FileNotFoundError(
            "No source video found. Run 'python ingest.py' first."
        )
    
    return video_files[0]


def load_best_clip_candidate() -> Dict:
    """Load the best clip candidate from JSON."""
    if not CLIP_CANDIDATES_JSON.exists():
        raise FileNotFoundError(
            "No clip candidates found. Run 'python detect_clips_v2.py' first."
        )
    
    with CLIP_CANDIDATES_JSON.open("r", encoding="utf-8") as file:
        candidates = json.load(file)
    
    if not candidates:
        raise ValueError("clip_candidates.json is empty.")
    
    return candidates[0]


def render_clip_simple(ffmpeg_path: str, source_video: Path, clip_candidate: Dict, transcript: Dict | None = None):
    """Render the selected clip with simple burned-in captions and a vertical frame."""
    FINAL_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    start_time = clip_candidate["start"]
    duration = clip_candidate["duration"]
    end_time = start_time + duration

    logger.info("=" * 60)
    logger.info("RENDERING CLIP WITH CAPTIONS")
    logger.info("=" * 60)
    logger.info(f"Source: {source_video}")
    logger.info(f"Start: {start_time}s | Duration: {duration}s | End: {end_time}s")
    logger.info(f"Output: {OUTPUT_CLIP}")

    try:
        if transcript and transcript.get("segments") and ENABLE_CAPTIONS:
            subtitle_path = create_subtitle_file(transcript, start_time, end_time)
            extract_clip_segment_with_captions(ffmpeg_path, source_video, OUTPUT_CLIP, start_time, duration, subtitle_path)
        else:
            extract_clip_segment(ffmpeg_path, source_video, OUTPUT_CLIP, start_time, duration)
        logger.info("\n" + "=" * 60)
        logger.info(f"Clip rendered successfully: {OUTPUT_CLIP}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Error rendering clip: {e}")
        raise


def create_subtitle_file(transcript: Dict, clip_start_time: float, clip_end_time: float) -> Path:
    """Create a readable SRT subtitle file for the selected clip window using the caption module."""
    subtitle_path = FINAL_CLIPS_DIR / "captions.srt"
    lines = []
    index = 1

    try:
        word_captions = extract_word_timestamps(transcript)
    except Exception as exc:
        logger.warning("Word-level caption timestamps unavailable, falling back to segment captions: %s", exc)
        word_captions = []

    def build_phrase_captions(items):
        phrases = []
        if not items:
            return phrases

        phrase_words = []
        phrase_start = None
        phrase_end = None

        for item in items:
            start = item.start_time_ms / 1000.0
            end = item.end_time_ms / 1000.0
            text = (item.word or "").strip()
            if not text:
                continue

            if end <= clip_start_time or start >= clip_end_time:
                continue

            actual_start = max(start, clip_start_time)
            actual_end = min(end, clip_end_time)
            if actual_end <= actual_start:
                continue

            if not phrase_words:
                phrase_words = [text]
                phrase_start = actual_start
                phrase_end = actual_end
            elif len(phrase_words) < 6 and (actual_start - phrase_end) <= 0.25:
                phrase_words.append(text)
                phrase_end = actual_end
            else:
                phrases.append((phrase_start, phrase_end, " ".join(phrase_words)))
                phrase_words = [text]
                phrase_start = actual_start
                phrase_end = actual_end

        if phrase_words:
            phrases.append((phrase_start, phrase_end, " ".join(phrase_words)))

        return phrases

    if word_captions:
        for start, end, text in build_phrase_captions(word_captions):
            if text:
                shifted_start = start - clip_start_time
                shifted_end = end - clip_start_time
                if shifted_end > shifted_start:
                    lines.append(format_srt_entry(index, shifted_start, shifted_end, text))
                    index += 1
    else:
        for segment in transcript.get("segments", []):
            start = float(segment.get("start", 0))
            end = float(segment.get("end", 0))
            text = (segment.get("text") or "").strip()

            if not text or end <= clip_start_time or start >= clip_end_time:
                continue

            actual_start = max(start, clip_start_time)
            actual_end = min(end, clip_end_time)
            if actual_end <= actual_start:
                continue

            # Shift caption times into clip-local time, since the clip begins at 0.
            lines.append(format_srt_entry(index, actual_start - clip_start_time, actual_end - clip_start_time, text))
            index += 1

    subtitle_path.write_text("\n\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return subtitle_path


def format_srt_entry(index: int, start: float, end: float, text: str) -> str:
    return "\n".join([
        str(index),
        f"{format_timestamp(start)} --> {format_timestamp(end)}",
        text,
    ])


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def extract_clip_segment(ffmpeg_path: str, source: Path, output: Path, 
                        start_time: float, duration: float):
    """Extract clip segment from source video using ffmpeg."""
    # Force output to target vertical resolution while preserving aspect ratio.
    scale_pad = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease," 
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )

    command = [
        ffmpeg_path,
        "-y",
        "-ss", str(start_time),
        "-i", str(source),
        "-t", str(duration),
        "-vf", scale_pad,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        str(output)
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        logger.info(f"Extracted segment: {output} ({duration}s)")
    except subprocess.CalledProcessError as e:
        raise VideoProcessingError(f"Failed to extract clip segment: {e.stderr.decode()}")


def extract_clip_segment_with_captions(ffmpeg_path: str, source: Path, output: Path,
                                      start_time: float, duration: float, subtitle_path: Path):
    """Extract clip segment and burn a visible text overlay onto the video."""
    # Single-step ffmpeg invocation: extract segment, burn subtitles, and scale/pad to target
    subtitle_file = subtitle_path.as_posix()
    subtitle_file = subtitle_file.replace(":", "\\:")

    scale_pad = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )

    filter_graph = (
        f"subtitles='{subtitle_file}':force_style='FontName=Arial,FontSize=36,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,"
        "Outline=2,Shadow=0,Alignment=2,MarginV=0'",
        scale_pad,
    )

    # Join filters with comma
    filter_chain = ",".join(filter_graph)

    command = [
        ffmpeg_path,
        "-y",
        "-ss", str(start_time),
        "-i", str(source),
        "-t", str(duration),
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        str(output)
    ]

    # Run ffmpeg and capture output for debugging
    debug_out = output.with_name(output.stem + "_burn_debug.mp4")
    # Replace last element of command with debug_out path
    cmd = list(command)
    cmd[-1] = str(debug_out)

    logger.info("Running ffmpeg command: %s", " ".join(map(str, cmd)))
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Save ffmpeg stdout+stderr to a log file for inspection
    log_path = FINAL_CLIPS_DIR / "ffmpeg_extract_with_captions.log"
    try:
        log_text = "".join(["STDOUT:\n", result.stdout or "", "\n\nSTDERR:\n", result.stderr or ""]) 
        log_path.write_text(log_text, encoding="utf-8")
    except Exception:
        logger.exception("Failed to write ffmpeg log file")

    if result.returncode != 0:
        logger.error("ffmpeg failed, see %s", log_path)
        raise VideoProcessingError(f"Failed to render clip with captions: {result.stderr}")

    # Move debug output to final output path (overwrite)
    try:
        import shutil as _sh
        _sh.move(str(debug_out), str(output))
    except Exception:
        logger.exception("Failed to move debug output to final output path")

    logger.info(f"Extracted segment with captions: {output} ({duration}s)")


def copy_video_file(source: Path, dest: Path, ffmpeg_path: str):
    """Copy video file using ffmpeg (fast stream copy)."""
    command = [
        ffmpeg_path,
        "-y",
        "-i", str(source),
        "-c", "copy",
        str(dest)
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        logger.info(f"Copied video: {dest}")
    except subprocess.CalledProcessError as e:
        raise VideoProcessingError(f"Failed to copy video: {e.stderr.decode()}")


if __name__ == "__main__":
    logger = setup_logging(level="INFO")
    
    ffmpeg = find_ffmpeg()
    source = find_source_video()
    best_clip = load_best_clip_candidate()
    transcript = None

    transcript_path = PROJECT_DIR / "data" / "transcripts" / "transcript.json"
    if transcript_path.exists():
        with transcript_path.open("r", encoding="utf-8") as file:
            transcript = json.load(file)
    
    render_clip_simple(ffmpeg, source, best_clip, transcript)
