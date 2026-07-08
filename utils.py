import logging
import sys
from pathlib import Path
from typing import Optional
import yaml

# Setup logging
def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Configure logging for all modules."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    if logger.hasHandlers():
        logger.handlers = []
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Load configuration
def load_config(config_path: Optional[Path] = None) -> dict:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

# Validation helpers
def validate_time_range(start: float, end: float, tolerance: float = 0.01) -> bool:
    """Validate that time range is valid (end > start)."""
    return end > start + tolerance

def validate_aspect_ratio(width: int, height: int, expected_ratio: str) -> bool:
    """Validate aspect ratio matches expected."""
    target_num, target_den = map(int, expected_ratio.split(':'))
    actual_ratio = width / height
    expected = target_num / target_den
    return abs(actual_ratio - expected) < 0.01

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))

# Error handling
class ClipperError(Exception):
    """Base exception for AI Clipper."""
    pass

class VideoProcessingError(ClipperError):
    """Error during video processing."""
    pass

class TranscriptionError(ClipperError):
    """Error during transcription."""
    pass

class FaceDetectionError(ClipperError):
    """Error during face detection."""
    pass

class CaptionError(ClipperError):
    """Error during caption rendering."""
    pass
