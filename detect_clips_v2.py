import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import re

from utils import load_config, ClipperError, setup_logging

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parent
TRANSCRIPT_JSON = PROJECT_DIR / "data" / "transcripts" / "transcript.json"
CLIPS_DIR = PROJECT_DIR / "data" / "clips"
CLIP_CANDIDATES_JSON = CLIPS_DIR / "clip_candidates.json"
CLIP_CANDIDATES_TEXT = CLIPS_DIR / "clip_candidates.txt"
ANALYSIS_REPORT = CLIPS_DIR / "analysis_report.json"

# Load configuration
config = load_config()
CLIP_CONFIG = config.get("clip_detection", {})

MIN_CLIP_SECONDS = CLIP_CONFIG.get("min_duration_seconds", 15)
MAX_CLIP_SECONDS = CLIP_CONFIG.get("max_duration_seconds", 45)
TOP_CLIP_COUNT = CLIP_CONFIG.get("top_clip_count", 5)
HOOK_WORDS = CLIP_CONFIG.get("hook_words", [])
TRANSITION_PHRASES = CLIP_CONFIG.get("transition_phrases", [])
HIGH_ENERGY_KEYWORDS = CLIP_CONFIG.get("high_energy_keywords", [])
SCORING_WEIGHTS = CLIP_CONFIG.get("scoring_weights", {})
MIN_CONFIDENCE_SCORE = CLIP_CONFIG.get("min_confidence_score", 0.3)
MIN_WORD_COUNT = CLIP_CONFIG.get("min_word_count", 25)
PAUSE_THRESHOLD = CLIP_CONFIG.get("pause_threshold_seconds", 1.0)


def load_transcript():
    """Load transcript from JSON file."""
    if not TRANSCRIPT_JSON.exists():
        raise FileNotFoundError(
            "No transcript found. Run 'python transcribe.py' first."
        )
    
    with TRANSCRIPT_JSON.open("r", encoding="utf-8") as file:
        return json.load(file)


def detect_hook_words(text: str) -> int:
    """Count occurrences of hook words in text."""
    score = 0
    lower_text = text.lower()
    for word in HOOK_WORDS:
        count = len(re.findall(r'\b' + re.escape(word) + r'\b', lower_text))
        score += count * SCORING_WEIGHTS.get("hook_word", 2)
    return score


def detect_transitions(text: str) -> int:
    """Detect transition phrases indicating natural clip boundaries."""
    score = 0
    lower_text = text.lower()
    for phrase in TRANSITION_PHRASES:
        if phrase.lower() in lower_text:
            score += SCORING_WEIGHTS.get("transition", 3)
    return score


def detect_high_energy(text: str) -> int:
    """Detect high-energy keywords indicating intensity."""
    score = 0
    lower_text = text.lower()
    for keyword in HIGH_ENERGY_KEYWORDS:
        if keyword.lower() in lower_text:
            score += SCORING_WEIGHTS.get("high_energy", 4)
    return score


def calculate_semantic_density(text: str) -> float:
    """
    Calculate semantic density (ratio of engagement signals to total words).
    Higher density = more engaging content.
    """
    if not text or len(text.split()) == 0:
        return 0.0
    
    signal_score = (
        detect_hook_words(text) + 
        detect_transitions(text) + 
        detect_high_energy(text)
    )
    
    word_count = len(text.split())
    return min(1.0, signal_score / (word_count / 10))  # Normalize


def detect_questions(text: str) -> bool:
    """Check if text contains questions."""
    return "?" in text


def detect_pause_after_segment(current_segment: Dict, next_segment: Dict) -> bool:
    """Detect natural pause between segments."""
    if not next_segment:
        return False
    
    pause_duration = next_segment["start"] - current_segment["end"]
    return pause_duration >= PAUSE_THRESHOLD


def detect_speaker_change(segments: List[Dict], start_idx: int, end_idx: int) -> bool:
    """
    Detect if there's a speaker change within segment range.
    (Placeholder - would need speaker identification in transcript)
    """
    return False


def calculate_word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def score_clip(text: str, duration: float, segment_index: int, segments: List[Dict]) -> Tuple[float, Dict]:
    """
    Calculate comprehensive clip score with detailed analysis.
    Returns: (score, analysis_details)
    """
    score = 0.0
    analysis = {
        "hooks": 0,
        "transitions": 0,
        "energy": 0,
        "questions": 0,
        "duration_bonus": 0,
        "word_count_bonus": 0,
        "semantic_density": 0.0,
        "penalties": 0,
    }
    
    # Hook word detection
    hook_score = detect_hook_words(text)
    analysis["hooks"] = hook_score
    score += hook_score
    
    # Transition detection
    transition_score = detect_transitions(text)
    analysis["transitions"] = transition_score
    score += transition_score
    
    # High energy keywords
    energy_score = detect_high_energy(text)
    analysis["energy"] = energy_score
    score += energy_score
    
    # Question detection
    if detect_questions(text):
        question_bonus = SCORING_WEIGHTS.get("question_mark", 3)
        analysis["questions"] = question_bonus
        score += question_bonus
    
    # Optimal duration bonus
    if MIN_CLIP_SECONDS <= duration <= MAX_CLIP_SECONDS:
        duration_bonus = SCORING_WEIGHTS.get("optimal_duration", 5)
        analysis["duration_bonus"] = duration_bonus
        score += duration_bonus
    
    # Word count bonus (substantial content)
    word_count = calculate_word_count(text)
    if word_count >= MIN_WORD_COUNT:
        word_bonus = SCORING_WEIGHTS.get("word_count_minimum", 2)
        analysis["word_count_bonus"] = word_bonus
        score += word_bonus
    
    # Semantic density scoring
    semantic_density = calculate_semantic_density(text)
    analysis["semantic_density"] = round(semantic_density, 3)
    score += semantic_density * SCORING_WEIGHTS.get("semantic_density", 5)
    
    # Speaker change penalty
    if detect_speaker_change(segments, segment_index, segment_index):
        penalty = SCORING_WEIGHTS.get("speaker_change_penalty", -10)
        analysis["penalties"] = penalty
        score += penalty
    
    # Normalize score
    confidence = min(1.0, max(0.0, score / 50.0))
    
    return round(score, 2), {**analysis, "confidence": round(confidence, 3)}


def build_clip_candidates(segments: List[Dict]) -> List[Dict]:
    """
    Build clip candidates using advanced semantic analysis.
    Finds optimal start/end points based on engagement signals.
    """
    candidates = []
    analysis_details = []
    
    for start_index in range(len(segments)):
        clip_segments = []
        clip_start = segments[start_index]["start"]
        clip_end = clip_start
        
        for segment in segments[start_index:]:
            clip_segments.append(segment)
            clip_end = segment["end"]
            duration = clip_end - clip_start
            
            # Skip if too short
            if duration < MIN_CLIP_SECONDS:
                continue
            
            # Stop if too long
            if duration > MAX_CLIP_SECONDS:
                break
            
            # Build clip text
            clip_text = " ".join(item["text"] for item in clip_segments)
            
            # Score the clip
            score, analysis = score_clip(clip_text, duration, start_index, segments)
            
            # Check minimum quality threshold
            if analysis["confidence"] < MIN_CONFIDENCE_SCORE:
                continue
            
            candidate = {
                "start": round(clip_start, 2),
                "end": round(clip_end, 2),
                "duration": round(duration, 2),
                "score": score,
                "confidence": analysis["confidence"],
                "text": clip_text,
                "segment_count": len(clip_segments),
                "analysis": analysis,
            }
            
            candidates.append(candidate)
            analysis_details.append({
                "start_segment": start_index,
                "candidate": candidate
            })
    
    # Sort by score descending
    candidates.sort(key=lambda clip: clip["score"], reverse=True)
    
    # Apply diversity filter (ensure top 5 don't overlap much)
    final_candidates = apply_diversity_filter(candidates[:TOP_CLIP_COUNT * 3])
    
    logger.info(f"Built {len(candidates)} total candidates, selected {len(final_candidates)} top candidates")
    
    return final_candidates[:TOP_CLIP_COUNT], analysis_details


def apply_diversity_filter(candidates: List[Dict], overlap_threshold: float = 0.3) -> List[Dict]:
    """
    Filter candidates to ensure diversity - avoid selecting overlapping clips.
    """
    if not candidates:
        return []
    
    diverse = [candidates[0]]
    
    for candidate in candidates[1:]:
        # Check overlap with existing diverse candidates
        has_overlap = False
        for existing in diverse:
            overlap_start = max(candidate["start"], existing["start"])
            overlap_end = min(candidate["end"], existing["end"])
            
            if overlap_end > overlap_start:
                overlap_ratio = (overlap_end - overlap_start) / min(
                    candidate["duration"], existing["duration"]
                )
                if overlap_ratio > overlap_threshold:
                    has_overlap = True
                    break
        
        if not has_overlap:
            diverse.append(candidate)
            if len(diverse) >= 5:
                break
    
    return diverse


def save_clip_candidates(candidates: List[Dict], analysis_details: List[Dict]):
    """Save clip candidates and analysis to files."""
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    with CLIP_CANDIDATES_JSON.open("w", encoding="utf-8") as file:
        json.dump(candidates, file, indent=2, ensure_ascii=False)
    
    # Save readable text
    with CLIP_CANDIDATES_TEXT.open("w", encoding="utf-8") as file:
        for index, clip in enumerate(candidates, start=1):
            file.write(f"{'='*60}\n")
            file.write(f"Clip {index}\n")
            file.write(f"{'='*60}\n")
            file.write(f"Time: {clip['start']}s → {clip['end']}s\n")
            file.write(f"Duration: {clip['duration']}s\n")
            file.write(f"Score: {clip['score']} | Confidence: {clip['confidence']}\n")
            file.write(f"Text: {clip['text']}\n\n")
            file.write(f"Analysis:\n")
            for key, value in clip['analysis'].items():
                file.write(f"  {key}: {value}\n")
            file.write("\n")
    
    # Save detailed analysis report
    with ANALYSIS_REPORT.open("w", encoding="utf-8") as file:
        json.dump({
            "total_candidates": len(candidates),
            "candidates": candidates,
            "detailed_analysis": analysis_details,
        }, file, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved clip candidates to: {CLIP_CANDIDATES_JSON}")
    logger.info(f"Saved readable candidates to: {CLIP_CANDIDATES_TEXT}")
    logger.info(f"Saved analysis report to: {ANALYSIS_REPORT}")


if __name__ == "__main__":
    logger = setup_logging(level="INFO")
    
    transcript = load_transcript()
    candidates, analysis = build_clip_candidates(transcript["segments"])
    save_clip_candidates(candidates, analysis)
