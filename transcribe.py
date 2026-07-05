import os
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel

video_url = "PASTE_YOUR_YOUTUBE_URL_HERE"

print("Downloading audio from YouTube... please wait...")

ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'outtmpl': 'yt_audio.%(ext)s',
    'overwrites': True,s
}

with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

print("\nAudio downloaded successfully! Booting up AI brain...")

model = WhisperModel("small", device="cpu", compute_type="int8")

print("AI Brain loaded. Transcribing the YouTube video now...\n")
segments, info = model.transcribe("yt_audio.m4a", beam_size=5)

print(f"Detected language: '{info.language}'")
print("--- Transcript ---")

for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")