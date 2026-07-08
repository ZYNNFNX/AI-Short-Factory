import logging
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import math

try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logging.warning("Pillow not installed. Caption rendering disabled.")

from utils import load_config, CaptionError

logger = logging.getLogger(__name__)

# Load configuration
config = load_config()
CAPTION_CONFIG = config.get("captions", {})
OUTPUT_CONFIG = config.get("output", {})

ENABLE_CAPTIONS = CAPTION_CONFIG.get("enable_captions", True)
BURN_INTO_VIDEO = CAPTION_CONFIG.get("burn_into_video", True)
ANIMATION_STYLE = CAPTION_CONFIG.get("animation_style", "fade_in")
ANIMATION_DURATION_MS = CAPTION_CONFIG.get("animation_duration_ms", 200)
WORD_HOLD_DURATION_EXTRA_MS = CAPTION_CONFIG.get("word_hold_duration_extra_ms", 50)
FONT_NAME = CAPTION_CONFIG.get("font_name", "Arial Bold")
FONT_SIZE_BASE = CAPTION_CONFIG.get("font_size_base", 48)
FONT_COLOR = CAPTION_CONFIG.get("font_color", "#FFFFFF")
HIGHLIGHT_COLOR = CAPTION_CONFIG.get("highlight_color", "#FFD700")
SHADOW_ENABLED = CAPTION_CONFIG.get("shadow_enabled", True)
SHADOW_OFFSET = CAPTION_CONFIG.get("shadow_offset", 3)
SHADOW_BLUR = CAPTION_CONFIG.get("shadow_blur", 5)
BACKGROUND_STYLE = CAPTION_CONFIG.get("background_style", "rounded_box")
BACKGROUND_COLOR = CAPTION_CONFIG.get("background_color", "#000000")
BACKGROUND_OPACITY = CAPTION_CONFIG.get("background_opacity", 0.85)
POSITION_Y_OFFSET = CAPTION_CONFIG.get("position_y_offset", 0.8)
HORIZONTAL_PADDING = CAPTION_CONFIG.get("horizontal_padding", 20)
VERTICAL_PADDING = CAPTION_CONFIG.get("vertical_padding", 15)
SYNC_TOLERANCE_MS = CAPTION_CONFIG.get("sync_tolerance_ms", 50)
MAX_LINE_WIDTH = CAPTION_CONFIG.get("max_line_width", 30)

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = OUTPUT_CONFIG.get("frame_rate", 30)


@dataclass
class WordCaption:
    """Represents a word with timing information."""
    word: str
    start_time_ms: float
    end_time_ms: float
    duration_ms: float
    word_index: int
    line_index: int
    
    def __post_init__(self):
        # Ensure duration is calculated correctly
        if self.duration_ms == 0:
            self.duration_ms = self.end_time_ms - self.start_time_ms


class CaptionAnimator:
    """Generates frame images with animated subtitles."""
    
    def __init__(self):
        if not PILLOW_AVAILABLE:
            raise CaptionError("Pillow not installed. Install via: pip install pillow")
        
        self.font_size = FONT_SIZE_BASE
        self.font_color = self.hex_to_rgb(FONT_COLOR)
        self.highlight_color = self.hex_to_rgb(HIGHLIGHT_COLOR)
        self.background_color = self.hex_to_rgb(BACKGROUND_COLOR)
        self.shadow_color = (0, 0, 0)  # Black shadow
        
        # Load font
        self.font = self._load_font()
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load font, with fallback to default if not found."""
        try:
            # Try common font paths
            font_paths = [
                Path("C:/Windows/Fonts/arialbd.ttf"),  # Windows bold Arial
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),  # Linux
                Path("/System/Library/Fonts/Helvetica.ttc"),  # macOS
            ]
            
            for path in font_paths:
                if path.exists():
                    return ImageFont.truetype(str(path), self.font_size)
            
            logger.warning(f"Font '{FONT_NAME}' not found, using default")
            return ImageFont.load_default()
        
        except Exception as e:
            logger.warning(f"Error loading font: {e}, using default")
            return ImageFont.load_default()
    
    def calculate_animation_progress(self, current_time_ms: float, word: WordCaption) -> float:
        """
        Calculate animation progress (0.0 to 1.0) for current frame.
        Handles different animation styles.
        """
        # Calculate position in word's timeline
        time_in_word = current_time_ms - word.start_time_ms
        
        if time_in_word < 0:
            return 0.0  # Before word starts
        if time_in_word > word.duration_ms:
            return 1.0  # After word ends
        
        # Animation phase calculation
        total_duration = word.duration_ms
        entrance_duration = min(ANIMATION_DURATION_MS, total_duration * 0.3)
        hold_duration = total_duration - entrance_duration
        
        if time_in_word < entrance_duration:
            # Entrance phase
            progress = time_in_word / entrance_duration
        else:
            # Hold phase
            progress = 1.0
        
        return min(1.0, max(0.0, progress))
    
    def apply_animation(self, image: Image.Image, word: WordCaption, current_time_ms: float, 
                       position: Tuple[int, int]) -> Image.Image:
        """
        Apply animation effect to word on image.
        Different styles: fade_in, slide_in, pop, typewriter, etc.
        """
        progress = self.calculate_animation_progress(current_time_ms, word)
        
        # Create transparent overlay for animation
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Determine animation style
        if ANIMATION_STYLE == "fade_in":
            alpha = int(255 * progress)
        elif ANIMATION_STYLE == "slide_in":
            alpha = 255
            position = (position[0] - int((1 - progress) * 50), position[1])
        elif ANIMATION_STYLE == "pop":
            alpha = int(255 * progress)
            scale = 0.8 + (progress * 0.2)  # 0.8 to 1.0
            self.font_size = int(FONT_SIZE_BASE * scale)
        elif ANIMATION_STYLE == "typewriter":
            alpha = 255
            # Show characters progressively
            progress_chars = int(len(word.word) * progress)
            if progress_chars == 0:
                return image
            word = WordCaption(
                word=word.word[:progress_chars],
                start_time_ms=word.start_time_ms,
                end_time_ms=word.end_time_ms,
                duration_ms=word.duration_ms,
                word_index=word.word_index,
                line_index=word.line_index,
            )
        else:
            alpha = 255
        
        # Draw word with shadow and background
        self._draw_word_with_background(
            draw, word.word, position, alpha
        )
        
        # Composite overlay onto base image
        return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    
    def _draw_word_with_background(self, draw: ImageDraw.ImageDraw, text: str, 
                                   position: Tuple[int, int], alpha: int):
        """Draw word with background box and shadow."""
        x, y = position
        
        # Get text bounding box
        bbox = draw.textbbox((x, y), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Add padding for background
        bg_x1 = x - HORIZONTAL_PADDING
        bg_y1 = y - VERTICAL_PADDING
        bg_x2 = x + text_width + HORIZONTAL_PADDING
        bg_y2 = y + text_height + VERTICAL_PADDING
        
        # Draw background with style
        if BACKGROUND_STYLE == "rounded_box":
            self._draw_rounded_rectangle(
                draw, [bg_x1, bg_y1, bg_x2, bg_y2],
                radius=10,
                fill=(*self.background_color, int(255 * BACKGROUND_OPACITY))
            )
        elif BACKGROUND_STYLE == "pill":
            self._draw_rounded_rectangle(
                draw, [bg_x1, bg_y1, bg_x2, bg_y2],
                radius=text_height // 2,
                fill=(*self.background_color, int(255 * BACKGROUND_OPACITY))
            )
        else:  # block
            draw.rectangle(
                [bg_x1, bg_y1, bg_x2, bg_y2],
                fill=(*self.background_color, int(255 * BACKGROUND_OPACITY))
            )
        
        # Draw shadow if enabled
        if SHADOW_ENABLED:
            shadow_color = (*self.shadow_color, alpha)
            draw.text(
                (x + SHADOW_OFFSET, y + SHADOW_OFFSET),
                text,
                font=self.font,
                fill=shadow_color
            )
        
        # Draw text
        text_color = (*self.font_color, alpha)
        draw.text(position, text, font=self.font, fill=text_color)
    
    @staticmethod
    def _draw_rounded_rectangle(draw: ImageDraw.ImageDraw, xy, radius: int = 10, **kwargs):
        """Draw rounded rectangle using PIL."""
        x1, y1, x2, y2 = xy
        draw.rectangle(
            [x1 + radius, y1, x2 - radius, y2],
            **kwargs
        )
        draw.rectangle(
            [x1, y1 + radius, x2, y2 - radius],
            **kwargs
        )
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, **kwargs)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, **kwargs)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, **kwargs)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, **kwargs)


def extract_word_timestamps(transcript: Dict) -> List[WordCaption]:
    """
    Extract word-level timestamps from Whisper transcript.
    Creates WordCaption objects with timing information.
    """
    if "segments" not in transcript:
        raise ValueError("Invalid transcript format - missing 'segments'")
    
    word_captions = []
    word_index = 0
    line_index = 0
    
    for segment in transcript["segments"]:
        segment_start = segment["start"]
        segment_text = segment["text"].strip()
        
        if not segment_text:
            continue
        
        words = segment_text.split()
        segment_duration = segment["end"] - segment_start
        
        # Distribute segment time across words
        time_per_word = segment_duration / len(words) if words else 0
        
        for word_idx, word in enumerate(words):
            # Calculate word timing (proportional distribution)
            word_start = segment_start + (word_idx * time_per_word)
            word_end = word_start + time_per_word
            
            word_caption = WordCaption(
                word=word,
                start_time_ms=word_start * 1000,  # Convert to milliseconds
                end_time_ms=word_end * 1000,
                duration_ms=(word_end - word_start) * 1000,
                word_index=word_index,
                line_index=line_index,
            )
            
            word_captions.append(word_caption)
            word_index += 1
            
            # Line break approximately every MAX_LINE_WIDTH characters
            if sum(len(wc.word) for wc in word_captions if wc.line_index == line_index) > MAX_LINE_WIDTH:
                line_index += 1
    
    logger.info(f"Extracted {len(word_captions)} word captions with {line_index + 1} lines")
    return word_captions


def generate_caption_frame(words: List[WordCaption], current_time_ms: float, 
                          animator: CaptionAnimator) -> Image.Image:
    """
    Generate a single frame with animated captions for current timestamp.
    """
    # Create base image
    base_image = Image.new('RGB', (TARGET_WIDTH, TARGET_HEIGHT), color=(0, 0, 0))
    
    # Group words by line
    lines_dict = {}
    for word in words:
        if word.line_index not in lines_dict:
            lines_dict[word.line_index] = []
        lines_dict[word.line_index].append(word)
    
    # Calculate vertical positioning
    num_lines = len(lines_dict)
    base_y = int(TARGET_HEIGHT * POSITION_Y_OFFSET)
    line_height = 70
    start_y = base_y - (num_lines * line_height // 2)
    
    # Draw each line
    current_image = base_image
    for line_idx in sorted(lines_dict.keys()):
        line_words = lines_dict[line_idx]
        
        # Calculate horizontal positioning (center text)
        line_text = " ".join(word.word for word in line_words)
        line_y = start_y + (line_idx * line_height)
        
        # Estimate text width and center it
        # This is approximate - better to measure actual rendered text
        line_x = TARGET_WIDTH // 2 - (len(line_text) * 12)  # ~12 pixels per character
        
        # Draw each word in line
        x_offset = 0
        for word in line_words:
            word_x = line_x + x_offset
            current_image = animator.apply_animation(
                current_image, word, current_time_ms, (word_x, line_y)
            )
            x_offset += len(word.word) * 12 + 20  # Word width + spacing
    
    return current_image


if __name__ == "__main__":
    """Test caption rendering."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Load transcript
    transcript_path = Path(__file__).parent / "data" / "transcripts" / "transcript.json"
    if not transcript_path.exists():
        print(f"Transcript not found: {transcript_path}")
        exit(1)
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = json.load(f)
    
    # Extract word captions
    words = extract_word_timestamps(transcript)
    
    # Create animator
    animator = CaptionAnimator()
    
    # Generate test frames
    test_times_ms = [0, 500, 1000, 1500, 2000]
    output_dir = Path(__file__).parent / "data" / "test_captions"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for time_ms in test_times_ms:
        frame = generate_caption_frame(words, time_ms, animator)
        frame.save(output_dir / f"caption_frame_{time_ms}.png")
        logger.info(f"Saved caption frame at {time_ms}ms")
