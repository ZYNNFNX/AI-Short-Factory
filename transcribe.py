import os
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel
from pydub import AudioSegment

# CONFIGURATION (ENTERPRISE CORE)
TARGET_KEYWORD = "routine"  #test keyword
AUDIO_FILE = "raw_source_audio.m4a"  # Unified file name
OUTPUT_CLIP = "result_short_clip.wav"

video_url = "https://www.youtube.com/watch?v=Szox9wD4HRU" #test video  

# 1. AUTOMATED ASSET INGESTION
if not os.path.exists(AUDIO_FILE):
    print("📥 Ingesting media asset from source URL...")
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'raw_source_audio.%(ext)s',
        'noplaylist': True,
        'overwrites': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    print("✅ Source asset downloaded successfully.")
else:
    print("🔄 Local asset detected. Bypassing network download ingestion.")

# 2. TIMESTAMPED ML TRANSCRIPTION PIPELINE
print("\n🧠 Initializing Machine Learning Engine (Whisper-Small Array)...")
model = WhisperModel("small", device="cpu", compute_type="int8")

print("🎙️ Processing audio telemetry and mapping structural timestamps...")
segments, info = model.transcribe(AUDIO_FILE, beam_size=5)

clip_start = None
clip_end = None

print("\n--- SYSTEM TRANSCRIPT LOG ---")
for segment in segments:
    print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    
    # Track target semantic window
    if TARGET_KEYWORD.lower() in segment.text.lower() and clip_start is None:
        clip_start = max(0, segment.start - 0.2)
        clip_end = segment.end + 0.3
        print(f"🎯 Target semantic boundary locked: {clip_start:.2f}s - {clip_end:.2f}s")
print("-----------------------------\n")

# 3. PRECISION WAVEFORM SEGMENTATION
if clip_start is not None and clip_end is not None:
    print(f"🎬 Segmenting waveform array from {clip_start:.2f}s to {clip_end:.2f}s...")
    
    start_ms = int(clip_start * 1000)
    end_ms = int(clip_end * 1000)
    
    full_audio = AudioSegment.from_file(AUDIO_FILE)
    short_clip = full_audio[start_ms:end_ms]
    
    short_clip.export(OUTPUT_CLIP, format="wav")
    print(f"🔥 Success! Exported pristine media sub-segment: '{OUTPUT_CLIP}'")
else:
    print("❌ Target phrase execution terminated: Keyword sequence not found in source text.")