# AI Clipper - 90-Step Execution Plan

## Project Overview
Transform the AI Clipper from basic clip detection into an intelligent vertical video generator with semantic analysis, dynamic face tracking, and animated captions.

---

## PHASE 1: Foundation & Planning (Steps 1-15)

### ✅ COMPLETED STEPS (4/4)
1. ✅ **Code Review Complete** - All 4 Python scripts analyzed for structure and dependencies
2. ✅ **Architecture Assessment** - Pipeline flow validated (ingest → transcribe → detect → render)
3. ✅ **Dependency Audit** - Identified required packages: yt-dlp, faster_whisper, opencv-python, mediaipe
4. ✅ **Edge Case Documentation** - Documented potential failures: corrupt videos, missing files, timing conflicts

### 📋 REMAINING FOUNDATION STEPS (5-15)
5. Create requirements.txt with all dependencies (yt-dlp, faster_whisper, opencv-python, mediapipe, pydub)
6. Create config.yaml for tunable parameters (hook words, confidence thresholds, video format settings)
7. Create utils.py for shared functions (logging, error handling, file management)
8. Design database schema for storing clip metadata and face detection results
9. Create .env template for API keys and paths
10. Setup logging infrastructure across all modules
11. Design data flow diagram for new features
12. Create test data fixtures (sample videos, transcripts)
13. Setup pytest configuration for unit testing
14. Document API contracts between modules
15. Create performance benchmarking framework

---

## PHASE 2: Highlight Detection Optimization (Steps 16-45)

### Feature: Advanced Semantic Density Analysis
- Detect hook words, transitions, high-energy keywords
- Calculate semantic density scores
- Identify optimal clip boundaries

#### Module: detect_clips_v2.py (Steps 16-45)
16. Expand HOOK_WORDS with 50+ engagement triggers (how, why, best, secret, exactly, imagine, consider, etc.)
17. Create TRANSITION_PHRASES list (now, here's the thing, so basically, let me explain, etc.)
18. Create HIGH_ENERGY_KEYWORDS list (amazing, incredible, breakthrough, game-changing, revolutionary, etc.)
19. Implement semantic_density() function to calculate word importance score
20. Implement transition_detection() function to find natural clip boundaries
21. Implement energy_level_analysis() to detect speaking pace and intensity changes
22. Implement question_answer_pair_detection() to link questions with their answers
23. Implement CAPS_EMPHASIS detection for transcription artifacts
24. Create weighting system for different signal types (hooks: 2pts, transitions: 3pts, energy: 4pts, questions: 5pts)
25. Implement context_window analysis (analyze surrounding segments for better decisions)
26. Implement sentiment_analysis() using lexicon-based approach
27. Implement clip_redundancy_check() to avoid overlapping candidates
28. Implement minimum_content_quality_check() (eliminate clips with too many filler words)
29. Create score_clip_v2() replacing old function with multi-dimensional scoring
30. Implement speaker_change_detection() to avoid mid-sentence speaker switches
31. Create pause_detection() to find natural breaking points (silence > 1 second)
32. Implement keyword_clustering() to group related topics within candidate
33. Create temporal_context_weighting() to favor clips with strong intro/outro
34. Implement diversity_filter() to ensure top 5 clips cover different topics
35. Add confidence_score to each candidate (0-1 scale)
36. Create json output with detailed metadata (why each clip ranked where)
37. Implement smoothing for extremely high/low scores
38. Create export_clip_analysis_report() for debugging
39. Add performance metrics (processing time, clips analyzed, avg score)
40. Implement caching layer for segment analysis
41. Create A/B test framework for scoring algorithm variations
42. Implement fallback scoring if advanced analysis fails
43. Add logging for each scoring decision
44. Create visualization helper for score distribution
45. Implement quality assurance checks for candidate validity

---

## PHASE 3: Auto-Reframe Execution with Face Detection (Steps 46-75)

### Feature: Dynamic Face Detection & 9:16 Vertical Crop
- Use MediaPipe/OpenCV for real-time face tracking
- Center vertical crop on speaker
- Handle multiple faces, profile shots, zoom-outs

#### Module: render_clip_v2.py with face_tracking.py (Steps 46-75)
46. Create face_tracking.py module for face detection logic
47. Implement MediaPipe Selfie Segmentation setup
48. Create load_video_with_opencv() to read video stream
49. Implement extract_face_region() using MediaPipe Face Detection
50. Create confidence_based_face_filtering() (only use high-confidence detections)
51. Implement face_center_calculation() using landmarks
52. Create temporal_smoothing() for face position (reduce jitter across frames)
53. Implement zoom_level_calculation() (detect if speaker close or far)
54. Create multi_face_handler() (choose primary speaker when multiple faces)
55. Implement profile_to_frontal_handling() (detect and handle side angles)
56. Create interpolation_for_missing_frames() (handle face detection gaps)
57. Implement kalman_filter() for smooth face tracking across frames
58. Create crop_box_calculation() for 9:16 aspect ratio centered on face
59. Implement edge_case_handling() (face too close to edge, multiple faces, no face)
60. Create frame_by_frame_crop_params() (generate crop box for each frame)
61. Implement dynamic_padding() to add buffer around face
62. Create zoom_preservation() (maintain zoom consistency within clip)
63. Implement performance_optimization() (process every Nth frame, interpolate)
64. Create video_codec_selector() (h264, h265, vp9 support)
65. Implement ffmpeg_command_builder() with dynamic crop parameters
66. Create batch_processing() for face detection on large videos
67. Implement GPU_acceleration() for faster processing
68. Create fallback_to_center_crop() if face detection fails
69. Implement frame_rate_handling() (work with 24/30/60fps)
70. Create quality_preservation() (minimize quality loss during crop)
71. Implement motion_blur_detection() (handle talking movement)
72. Create debug_overlay_mode() (visualize crop boxes for testing)
73. Implement frame_skipping() for detection efficiency
74. Create aspect_ratio_validation() (ensure 9:16 output)
75. Implement final_video_validation() (check codec, duration, dimensions)

---

## PHASE 4: Automated Captions (Steps 76-90)

### Feature: Word-by-Word Animated Subtitles
- Extract Whisper word-level timestamps
- Animate text entrance/exit
- Burn into 9:16 video

#### Module: caption_renderer.py (Steps 76-90)
76. Create caption_renderer.py module
77. Implement extract_word_timestamps() from Whisper output
78. Create TextAnimation enum (fade_in, slide_in, pop, typewriter, etc.)
79. Implement calculate_word_duration() for each word
80. Create font_selector() (download/cache fonts for mobile look)
81. Implement font_size_calculator() (scale based on word count per line)
82. Create color_scheme_generator() (accent first word, highlight keywords)
83. Implement background_shape_selector() (rounded box, pill, block)
84. Create shadow_effect_builder() (depth for mobile readability)
85. Implement animation_timing_calculator() (enter at word start, exit at word end)
86. Create frame_generation() (PIL/Pillow to generate subtitle frames)
87. Implement overlay_optimization() (efficient compositing)
88. Create hardcoded_subtitle_rendering() (burn subtitles into video)
89. Implement ffmpeg_subtitle_stream() (alternative method)
90. Create caption_quality_testing() (readability, timing accuracy, mobile preview)

---

## Feature Breakdown by Priority

### TIER 1 - Critical Path (Enables other features)
- Steps 5-7: Infrastructure setup
- Steps 16-25: Core semantic analysis
- Steps 46-53: Face detection foundation

### TIER 2 - High Value (Major new capabilities)
- Steps 26-38: Advanced semantic features
- Steps 54-68: Complete face tracking
- Steps 76-82: Caption system foundation

### TIER 3 - Polish & Optimization
- Steps 39-45: Analysis refinement
- Steps 69-75: Performance & quality
- Steps 83-90: Caption finishing

---

## Technical Dependencies

### New Packages to Install
```
opencv-python>=4.8.0
mediapipe>=0.10.0
pydub>=0.25.1
pillow>=10.0.0
nltk>=3.8
textblob>=0.17.1
pyyaml>=6.0
python-dotenv>=1.0.0
```

### Refactored Modules
- `detect_clips.py` → `detect_clips_v2.py` (backward compatible)
- `render_clip.py` → `render_clip_v2.py` + new `face_tracking.py`
- NEW: `caption_renderer.py`
- NEW: `utils.py`
- NEW: `config.yaml`

---

## Success Metrics
✅ Step 4: Code passes linting and type checking
✅ Step 15: All modules have >90% test coverage
✅ Step 45: Clip detection accuracy improves by 40%
✅ Step 75: Face tracking maintains <5px jitter
✅ Step 90: Captions sync within 50ms of word timestamps

