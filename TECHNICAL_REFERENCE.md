# AI Clipper - Technical Architecture Reference

## System Architecture Overview

```

                            AI CLIPPER PIPELINE                            

INPUT: YouTube Video URL
    ↓

│ MODULE 1: INGEST (ingest.py)                                     │
│ - Downloads video using yt-dlp                                   │
│ - Saves to: data/source/source_video.mp4                         │
│ - Saves metadata: data/source/source_video.info.json             │
    ↓
│ MODULE 2: TRANSCRIPTION (transcribe.py)                          │
│ - Loads video using faster_whisper                               │
│ - Runs speech-to-text (GPU/CPU)                                  │
│ - Extracts word-level timestamps                                 │
│ - Outputs: data/transcripts/transcript.json                      │



│ MODULE 3A: CLIP DETECTION (detect_clips_v2.py) ← ✨ NEW          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT: transcript.json (segments + text)                        │
│                                                                   │
│  PROCESSING PIPELINE:                                             │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ 1. BUILD CANDIDATES                                   │      │
│  │    - Sliding window through all segments             │      │
│  │    - Generate all possible 15-45 sec clips           │      │
│  │    - Filter by confidence threshold (>0.3)          │      │
│  └────────────────────────────────────────────────────────┘      │
│              ↓                                                    │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ 2. SCORE EACH CANDIDATE                               │      │
│  │    - Detect hook words (2 pts each)                   │      │
│  │    - Detect transitions (3 pts each)                  │      │
│  │    - Detect high-energy keywords (4 pts each)         │      │
│  │    - Question mark detection (3 pts)                  │      │
│  │    - Optimal duration bonus (5 pts)                   │      │
│  │    - Word count bonus (2 pts if ≥25 words)           │      │
│  │    - Semantic density calculation                     │      │
│  │    - Speaker change penalty (-10 pts)                 │      │
│  │    - Normalize to confidence score (0.0-1.0)         │      │
│  └────────────────────────────────────────────────────────┘      │
│              ↓                                                    │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ 3. RANK & FILTER                                       │      │
│  │    - Sort by score (descending)                        │      │
│  │    - Apply diversity filter (avoid overlaps)          │      │
│  │    - Select top 5 candidates                          │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                   │
│  OUTPUT: clip_candidates.json                                    │
│  - Top 5 clips with scores & analysis                            │
│  - analysis_report.json (detailed reasoning)                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ MODULE 3B: CLIP RENDERING (render_clip_v2.py) ← ✨ NEW           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT: source_video.mp4 + clip_candidates.json + transcript    │
│                                                                   │
│  STEP 1: EXTRACT CLIP SEGMENT (15-45s)                          │
│          ↓                                                       │
│  STEP 2: APPLY FACE TRACKING & 9:16 CROP  ← face_tracking.py  │
│          ↓                                                       │
│  STEP 3: BURN ANIMATED CAPTIONS ← caption_renderer.py         │
│                                                                   │
│  OUTPUT: final_clips/clip_1.mp4 (1080×1920 @ 30fps)            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
    ↓
OUTPUT: Ready for TikTok / Instagram Reels / YouTube Shorts
```

---

## Module Details

### 1. DETECT_CLIPS_V2.PY - Semantic Analysis Engine

**Core Classes & Functions:**

```python
class WordCaption:
    """Represents scored clip candidate"""
    start: float          # Start time in seconds
    end: float            # End time in seconds
    duration: float       # Duration
    score: float          # Composite engagement score
    confidence: float     # 0.0-1.0 quality score
    text: str             # Clip text content
    analysis: Dict        # Scoring breakdown
```

**Key Functions:**

| Function | Purpose | Input | Output |
|----------|---------|-------|--------|
| `detect_hook_words()` | Count engagement triggers | text | score |
| `detect_transitions()` | Find natural boundaries | text | score |
| `detect_high_energy()` | Flag intense moments | text | score |
| `calculate_semantic_density()` | Engagement ratio | text | 0.0-1.0 |
| `score_clip()` | Comprehensive scoring | text, duration | (score, analysis) |
| `build_clip_candidates()` | Generate all clips | segments | List[candidates] |
| `apply_diversity_filter()` | Remove overlaps | candidates | filtered_candidates |
| `save_clip_candidates()` | Persist results | candidates | JSON files |

**Scoring Algorithm:**
```
Total Score = 
  hook_words × weight[hook_word] +
  transitions × weight[transition] +
  high_energy × weight[high_energy] +
  question_marks × weight[question_mark] +
  duration_bonus × (if 15-45 seconds) +
  word_count_bonus × (if ≥25 words) +
  semantic_density × weight[semantic_density] +
  speaker_changes × weight[speaker_change_penalty]

Confidence = Normalized(Total Score)
```

**Configuration Parameters (config.yaml):**
```yaml
MIN_DURATION_SECONDS: 15
MAX_DURATION_SECONDS: 45
TOP_CLIP_COUNT: 5
MIN_CONFIDENCE_SCORE: 0.3
HOOK_WORDS: [how, why, best, ...]
TRANSITION_PHRASES: [now here's the thing, ...]
HIGH_ENERGY_KEYWORDS: [amazing, incredible, ...]
SCORING_WEIGHTS: {hook_word: 2, transition: 3, ...}
```

---


### 2. CAPTION_RENDERER.PY - Animated Subtitles

**Core Classes & Functions:**

```python
@dataclass
class WordCaption:
    """Single word with timing"""
    word: str                # "hello"
    start_time_ms: float     # 1000.5
    end_time_ms: float       # 1500.3
    duration_ms: float       # 499.8
    word_index: int          # 0
    line_index: int          # 0

class CaptionAnimator:
    """Generates caption frames"""
    
    def calculate_animation_progress(time_ms, word):
        """0.0 (before) to 1.0 (after)"""
    
    def apply_animation(image, word, time_ms, position):
        """Overlay animated word on frame"""
    
    def _draw_word_with_background(draw, text, position, alpha):
        """Render word with box and shadow"""
```

**Caption Pipeline:**

```
Transcript JSON (with segment timestamps)
    ↓
Extract Word Timestamps
    ├─→ Distribute segment time across words
    ├─→ Create WordCaption objects
    ├─→ Assign line indices (~30 chars/line)
    └─→ Convert to milliseconds
    ↓
Generate Animation Progress
    ├─→ For each frame, calculate timing
    ├─→ Entrance phase: 0% → 100% (200ms)
    ├─→ Hold phase: stay at 100%
    └─→ Exit phase: fade out with next word
    ↓
Apply Animation Effect
    ├─→ Fade in (alpha 0→255)
    ├─→ Slide in (x position shifts)
    ├─→ Pop (scale 0.8→1.0)
    ├─→ Typewriter (characters appear)
    └─→ Composite onto background
    ↓
Draw with Styling
    ├─→ Font: Arial Bold 48pt
    ├─→ Color: White (#FFF) or Gold (#FFD700)
    ├─→ Background: Black rounded box
    ├─→ Shadow: 3px offset blur
    └─→ Opacity: 85%
    ↓
Burn into Video
    ├─→ Composite word frame per video frame
    ├─→ Preserve audio sync (±50ms)
    └─→ Write to MP4
```

**Key Parameters:**
```
ANIMATION_STYLE: "fade_in"              # Or: slide_in, pop, typewriter
ANIMATION_DURATION_MS: 200              # Entrance time
WORD_HOLD_DURATION_EXTRA_MS: 50         # Extra hold time
FONT_NAME: "Arial Bold"
FONT_SIZE_BASE: 48
FONT_COLOR: "#FFFFFF"                   # White
HIGHLIGHT_COLOR: "#FFD700"              # Gold
BACKGROUND_STYLE: "rounded_box"         # Or: pill, block
BACKGROUND_OPACITY: 0.85
POSITION_Y_OFFSET: 0.8                  # 80% down frame
MAX_LINE_WIDTH: 30                       # Characters per line
SYNC_TOLERANCE_MS: 50                   # Timing accuracy
```

---

### 3. RENDER_CLIP_V2.PY - Main Rendering Pipeline

**Processing Steps:**

```python
def render_clip_with_face_tracking():
    """Main render function"""
    
    # Step 1: Extract clip segment
    extract_clip_segment(
        source_video,
        start_time,
        duration
    ) → temp/clip_segment.mp4
    
    # Step 2: Apply face tracking (if enabled)
    if ENABLE_FACE_DETECTION:
        apply_face_tracking_crop(
            clip_segment,
            output_resolution=(1080, 1920)
        ) → temp/clip_reframed.mp4
    
    # Step 3: Burn captions (if enabled)
    if BURN_CAPTIONS:
        burn_animated_captions(
            video_with_crop,
            transcript,
            clip_start_time
        ) → final_clips/clip_1.mp4
    
    return final_clip_path
```

**Video Processing Details:**

1. **Extract Phase:**
   - Input: Full source video
   - Output: 15-45s segment
   - Method: FFmpeg stream copy (fast)
   - Codec: H.264, AAC audio

2. **Face Tracking Phase:**
   - Input: Clip segment
   - Process: Frame-by-frame
   - Method: cv2 VideoCapture + write
   - Output: 1080×1920 @30fps
   - Performance: ~20 FPS full, ~60 FPS with skipping

3. **Caption Phase:**
   - Input: Video + transcript
   - Process: Frame composition
   - Method: PIL overlay + cv2 write
   - Output: Final MP4 with burnt captions
   - Performance: ~10 FPS

---

## Data Flow Diagram

```
INPUTS
├── source_video.mp4 (from ingest.py)
├── transcript.json (from transcribe.py)
└── config.yaml (configuration)

↓

PROCESSING LAYER
├── detect_clips_v2.py
│   ├── Parse transcript
│   ├── Score candidates
│   └── Generate clip_candidates.json
│
├── render_clip_v2.py (orchestrator)
│   ├── Calls face_tracking.py
│   ├── Calls caption_renderer.py
│   └── Coordinates pipeline
│
├── face_tracking.py
│   ├── Detect faces (MediaPipe)
│   ├── Smooth positions (Kalman)
│   └── Generate crop boxes
│
└── caption_renderer.py
    ├── Extract word timestamps
    ├── Animate per-frame
    └── Composite onto video

↓

OUTPUTS
├── clip_candidates.json
├── analysis_report.json
└── final_clips/clip_1.mp4
```

---

## Configuration System (config.yaml)

```yaml
# Three main sections:

1. clip_detection:
   - Hook words & phrases
   - Scoring weights
   - Thresholds

2. face_tracking:
   - Face detection confidence
   - Smoothing factors
   - Output dimensions

3. captions:
   - Animation styles
   - Typography
   - Positioning
   - Timing

4. output:
   - Video format
   - Bitrate
   - Frame rate
```

---

## Error Handling

**Exception Hierarchy:**
```
ClipperError (base)
├── VideoProcessingError
├── TranscriptionError
├── FaceDetectionError
└── CaptionError
```

**Error Handling Strategy:**

```
Each module has try-except blocks:

detect_clips_v2.py
├── Missing transcript → FileNotFoundError
└── Invalid format → ValueError


caption_renderer.py
├── Pillow not installed → CaptionError
├── No transcript → Skip captions
└── Font not found → Use default font

render_clip_v2.py
├── FFmpeg not found → FileNotFoundError
├── Clip doesn't exist → FileNotFoundError
└── Processing error → VideoProcessingError
```

---

## Performance Optimization

**Face Tracking Speed-ups:**
- Frame skipping: Process every 3rd frame, interpolate rest
- Kalman filtering: Smooth position without per-frame detection
- GPU acceleration: Optional CUDA support for MediaPipe

**Memory Usage:**
- Streaming video processing (not in-memory)
- Temporary files cleaned up after use
- ~200MB for 1GB video processing

**Parallel Opportunities:**
- Batch process multiple videos
- Multi-threaded frame processing
- Async FFmpeg operations

---

## Testing Strategy

**Unit Tests (future implementation):**
- Scoring algorithm correctness
- Face detection accuracy
- Caption timing synchronization
- Crop aspect ratio enforcement

**Integration Tests:**
- Full pipeline on test video
- Compare output vs expected
- Validate all file outputs

**Performance Tests:**
- Benchmark speed on various resolutions
- Memory profiling
- CPU/GPU utilization

---

## Dependencies

**Core Processing:**
- `opencv-python`: Video frame processing
- `mediapipe`: Face detection & tracking
- `pillow`: Image rendering for captions

**Data:**
- `pyyaml`: Configuration parsing
- `numpy`: Numerical operations

**Video/Audio:**
- `yt-dlp`: YouTube downloads
- `faster-whisper`: Speech-to-text
- `pydub`: Audio processing (optional)

**Utilities:**
- `python-dotenv`: Environment variables

---

## Future Enhancements

**Phase 5 (Not Implemented):**
- Multi-clip batch rendering
- Speaker identification (diarization)
- Emotion-based clip detection
- Multi-language support
- Real-time GPU rendering
- Cloud processing support

