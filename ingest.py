from pathlib import Path
from yt_dlp import YoutubeDL


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
SOURCE_DIR = DATA_DIR / "source"

VIDEO_OUTPUT_TEMPLATE = str(SOURCE_DIR / "source_video.%(ext)s")
METADATA_OUTPUT = SOURCE_DIR / "metadata.json"


def ensure_dirs():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)


def download_source_video(video_url: str):
    ensure_dirs()

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": VIDEO_OUTPUT_TEMPLATE,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "overwrites": True,
        "writeinfojson": True,
        "quiet": False,
    }

    print("Downloading source video...")

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    print("Source video downloaded.")
    print(f"Title: {info.get('title')}")
    print(f"Duration: {info.get('duration')} seconds")
    print(f"Uploader: {info.get('uploader')}")

    return info


if __name__ == "__main__":
    url = input("Enter video URL: ").strip()

    if not url:
        raise ValueError("A video URL is required.")

    download_source_video(url)
