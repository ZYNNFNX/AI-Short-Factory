import json
import traceback
from pathlib import Path
from utils import setup_logging
import render_clip_v2 as rc

logger = setup_logging(level='DEBUG')

try:
    ffmpeg = rc.find_ffmpeg()
    print('FFMPEG:', ffmpeg)
    src = rc.find_source_video()
    print('SOURCE:', src)
    best = rc.load_best_clip_candidate()
    print('BEST CLIP:', best.get('start'), best.get('duration'))

    transcript_path = rc.PROJECT_DIR / 'data' / 'transcripts' / 'transcript.json'
    transcript = None
    if transcript_path.exists():
        with transcript_path.open('r', encoding='utf-8') as f:
            transcript = json.load(f)
    subtitle = rc.create_subtitle_file(transcript, best['start'], best['start'] + best['duration'])
    print('SUBTITLE:', subtitle)

    out = rc.FINAL_CLIPS_DIR / 'clip_1_debug_out.mp4'
    rc.extract_clip_segment_with_captions(ffmpeg, src, out, best['start'], best['duration'], subtitle)
    print('DONE')
except Exception as e:
    print('EXCEPTION:')
    traceback.print_exc()
