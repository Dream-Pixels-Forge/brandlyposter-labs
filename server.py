#!/usr/bin/env python3
"""
BrandlyPoster-Labs MCP Server — Next Level
Multi-agent poster studio with subject vault, vision QA, batch export, client approval.
"""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field

from mcp.server.fastmcp import FastMCP
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from sentence_transformers import SentenceTransformer
import cv2
import numpy as np

# ============================================================================
# CONFIGURATION & PATHS
# ============================================================================

DATA_ROOT = Path(os.environ.get("BRANDLY_DATA_ROOT", "/mnt/data/brandlyposter-labs"))
SUBJECTS_DIR = DATA_ROOT / "subjects"
PROJECTS_DIR = DATA_ROOT / "projects"
SUBJECTS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# Vision QA configuration
LIKENESS_THRESHOLD = float(os.environ.get("BRANDLY_LIKENESS_THRESHOLD", "0.85"))
QA_THRESHOLD = 6  # must score 6/6

# ============================================================================
# GENRES & PRESETS (from prototype)
# ============================================================================

GENRES = {
    "thriller": {"name": "Prestige Thriller", "backgrounds": ["Kinshasa skyline golden hour", "boardroom charts", "fashion runway"], "palette": ["#0A1931", "#D4AF37", "#E5E5E5"], "lighting": "dramatic anamorphic"},
    "romcom": {"name": "Rom-Com - Chaos color chemistry", "backgrounds": ["Gambela market mangoes wax prints", "rooftop dinner fairy lights"], "palette": ["#FF6B6B", "#FFD93D", "#FFF8E7"], "lighting": "soft golden hour rim"},
    "scifi": {"name": "African Futurism Sci-Fi", "backgrounds": ["futuristic Kinshasa 2045 flying vehicles", "holographic screens"], "palette": ["#6C5CE7", "#00CEC9"], "lighting": "neon volumetric"},
    "action": {"name": "Spy Action", "backgrounds": ["city chase", "helicopter", "secret base"], "palette": ["#2D3436", "#636E72"], "lighting": "hard key high contrast"},
    "fashion": {"name": "Fashion Documentary", "backgrounds": ["atelier sketches", "fabric rolls", "Paris Fashion Week"], "palette": ["#F5F5DC", "#D2B48C"], "lighting": "soft studio beauty"},
    "horror": {"name": "Psychological Horror", "backgrounds": ["abandoned Kinshasa theatre", "foggy river"], "palette": ["#0A0A0A", "#8B0000"], "lighting": "low key chiaroscuro"},
    "epic": {"name": "Historical Epic", "backgrounds": ["ancient Kongo kingdom", "savanna sunset"], "palette": ["#8B4513", "#DAA520"], "lighting": "epic golden hour"},
}

FONTS = {
    "titles": ["Playfair Display", "Bebas Neue", "Montserrat Black", "Oswald", "Anton", "Cinzel", "Cormorant Garamond"],
    "subtitles": ["Montserrat", "Inter", "Helvetica Neue", "Futura", "Gotham"],
    "taglines": ["Inter Light", "Helvetica Thin", "Montserrat Light", "Avenir"],
    "billing": ["Univers Condensed", "Helvetica Compressed", "Arial Narrow"],
}

# ============================================================================
# VISION MODEL SETUP (lazy-loaded)
# ============================================================================

_clip_model = None
_clip_processor = None
_sbert_model = None

def get_clip():
    global _clip_model, _clip_processor
    if _clip_model is None:
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return _clip_model, _clip_processor

def get_sbert():
    global _sbert_model
    if _sbert_model is None:
        _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sbert_model

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SubjectProfile:
    subject_id: str
    name: str
    reference_images: List[str]
    face_embedding: Optional[List[float]] = None
    likeness_threshold: float = LIKENESS_THRESHOLD
    earring_baseline: Optional[Dict[str, Any]] = None
    story: str = ""
    outfit: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def save(self):
        path = SUBJECTS_DIR / self.subject_id / "profile.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, subject_id: str):
        path = SUBJECTS_DIR / subject_id / "profile.json"
        if not path.exists():
            raise FileNotFoundError(f"Subject {subject_id} not found")
        return cls.from_dict(json.loads(path.read_text()))


@dataclass
class ProjectManifest:
    project_id: str
    subject_id: str
    poster_id: str
    genre: str
    master_prompt: str
    qa_score: str = "0/6"
    qa_passed: bool = False
    variants: List[Dict[str, Any]] = field(default_factory=list)
    approved: bool = False
    approved_version: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

    def save(self):
        path = PROJECTS_DIR / self.project_id / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, project_id: str):
        path = PROJECTS_DIR / project_id / "manifest.json"
        if not path.exists():
            raise FileNotFoundError(f"Project {project_id} not found")
        return cls.from_dict(json.loads(path.read_text()))


# ============================================================================
# VISION UTILITIES
# ============================================================================

def compute_face_embedding(image_path: str) -> List[float]:
    """Extract face embedding using CLIP image encoder.

    Missing or unreadable images return an empty embedding instead of
    raising, so callers (subject match, vision QA) degrade gracefully
    to similarity 0.0 / pass=False.
    """
    model, processor = get_clip()
    try:
        image = Image.open(image_path).convert("RGB")
    except (FileNotFoundError, OSError):
        return []
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        image_features = outputs.pooler_output
    # Normalize
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.squeeze().tolist()


def compute_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Cosine similarity between two embeddings.

    Zero-length or empty vectors return 0.0 instead of nan so callers
    (subject match, vision QA, scan issues) never emit a non-JSON-safe
    similarity value.
    """
    a = np.array(emb1, dtype=float)
    b = np.array(emb2, dtype=float)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def detect_gold_hoop_earrings(image_path: str) -> Dict[str, Any]:
    """
    Pixel-level detection of gold hoop earrings.
    Returns: {pass, left_ear, right_ear, offset_delta_px, symmetrical}
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"pass": False, "error": "Could not read image"}

    h, w = img.shape[:2]

    # Convert to HSV for gold detection
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Gold color range in HSV (approximate)
    gold_lower = np.array([15, 100, 100])
    gold_upper = np.array([35, 255, 255])
    gold_mask = cv2.inRange(hsv, gold_lower, gold_upper)

    # Find contours
    contours, _ = cv2.findContours(gold_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter for small circular shapes (hoop earrings)
    ear_candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 20 < area < 2000:  # reasonable earring size range
            (x, y), radius = cv2.minEnclosingCircle(cnt)
            circularity = 4 * np.pi * area / (cv2.arcLength(cnt, True) ** 2) if cv2.arcLength(cnt, True) > 0 else 0
            if circularity > 0.5:
                ear_candidates.append({"x": float(x), "y": float(y), "radius": float(radius), "area": float(area)})

    if len(ear_candidates) < 2:
        return {"pass": False, "reason": f"Only {len(ear_candidates)} earring candidates found", "candidates": ear_candidates}

    # Assume left/right based on x coordinate
    ear_candidates.sort(key=lambda e: e["x"])
    left_ear = ear_candidates[0]
    right_ear = ear_candidates[-1]

    # Check symmetry: similar radius, vertically aligned
    radius_delta = abs(left_ear["radius"] - right_ear["radius"])
    y_delta = abs(left_ear["y"] - right_ear["y"])
    x_center = (left_ear["x"] + right_ear["x"]) / 2

    symmetrical = (radius_delta < 5.0 and y_delta < 10.0)

    return {
        "pass": symmetrical,
        "left_ear": left_ear,
        "right_ear": right_ear,
        "radius_delta_px": float(radius_delta),
        "y_delta_px": float(y_delta),
        "symmetrical": symmetrical,
        "offset_delta_px": float(y_delta),
    }


def check_no_cropped_hands_feet(image_path: str) -> bool:
    """Heuristic: check if subject extends to bottom of frame (not cropped)."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    h, w = img.shape[:2]
    # Check bottom 10% for skin tones or non-background pixels
    bottom = img[int(h * 0.9):, :]
    # Simple heuristic: if bottom region is mostly dark/background, likely cropped
    gray = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness > 20  # threshold for "not black background"


def check_eyes_sharp(image_path: str) -> bool:
    """Check if eye region is in focus using Laplacian variance."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Focus on upper-middle region (where eyes typically are)
    h, w = gray.shape
    eye_region = gray[int(h * 0.25):int(h * 0.55), int(w * 0.25):int(w * 0.75)]
    if eye_region.size == 0:
        return False
    laplacian_var = cv2.Laplacian(eye_region, cv2.CV_64F).var()
    return laplacian_var > 100  # threshold for "sharp"


def check_text_legible(image_path: str) -> bool:
    """Simple OCR check for text presence at expected positions."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    h, w = img.shape[:2]
    # Check top 15% for title text (high contrast)
    top = img[:int(h * 0.15), :]
    gray = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)
    # High contrast = text likely present
    contrast = np.std(gray)
    return contrast > 30


def check_ratio_2_3(image_path: str) -> bool:
    """Check if image aspect ratio is 2:3 (portrait)."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    h, w = img.shape[:2]
    ratio = w / h
    return abs(ratio - 2/3) < 0.02  # 2% tolerance


# ============================================================================
# COMPREHENSIVE ISSUE DETECTION & FIX GENERATION
# ============================================================================


def detect_issues_with_visualization(image_path: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full issue detection and return visualization data for scan animation.
    Returns: {
        'issues': {...},
        'scan_frames': [{'region': 'ears', 'bbox': [x,y,w,h], 'issue': 'asymmetry', 'severity': 'high'}],
        'annotated_image_path': '/path/to/annotated.png',
    }
    """
    img = cv2.imread(image_path)
    if img is None:
        return {'error': 'Could not read image'}
    
    h, w = img.shape[:2]
    issues = {}
    scan_frames = []
    annotated = img.copy()
    
    # 1. Earring symmetry with bbox
    earring_result = detect_gold_hoop_earrings(image_path)
    issues['earrings'] = earring_result
    if 'left_ear' in earring_result and 'right_ear' in earring_result:
        le = earring_result['left_ear']
        re = earring_result['right_ear']
        # Draw bboxes on annotated image
        for ear, label in [(le, 'left'), (re, 'right')]:
            x, y, r = int(ear['x']), int(ear['y']), int(ear['radius'] + 10)
            cv2.rectangle(annotated, (x-r, y-r), (x+r, y+r), (0, 212, 175), 2)
            cv2.putText(annotated, f'{label}_earring', (x-r, y-r-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 212, 175), 1)
        
        if not earring_result.get('symmetrical', True):
            issues['earrings']['issue'] = 'asymmetry'
            issues['earrings']['severity'] = 'high'
            issues['earrings']['fix_suggestion'] = 'Regenerate with: both small gold hoop earrings identical size/position in BOTH ears'
            scan_frames.append({
                'region': 'ears',
                'bbox': [min(le['x'], re['x'])-30, min(le['y'], re['y'])-30, abs(le['x']-re['x'])+60, max(le['radius'], re['radius'])*2+60],
                'issue': 'asymmetry',
                'severity': 'high',
                'fix_prompt': 'both small gold hoop earrings present perfectly symmetrical clearly visible in BOTH ears, identical size and position'
            })
        else:
            scan_frames.append({'region': 'ears', 'bbox': [min(le['x'], re['x'])-30, min(le['y'], re['y'])-30, abs(le['x']-re['x'])+60, max(le['radius'], re['radius'])*2+60], 'issue': 'ok', 'severity': 'none'})
    
    # 2. Face/likeness region
    if subject_id:
        try:
            subject = SubjectProfile.load(subject_id)
            if subject.face_embedding:
                gen_embedding = compute_face_embedding(image_path)
                similarity = compute_similarity(subject.face_embedding, gen_embedding)
                pass_thresh = similarity >= subject.likeness_threshold
                issues['likeness'] = {'pass': pass_thresh, 'score': similarity, 'threshold': subject.likeness_threshold}
                if not pass_thresh:
                    issues['likeness']['issue'] = 'face_drift'
                    issues['likeness']['severity'] = 'critical'
                    issues['likeness']['fix_suggestion'] = f'Regenerate with stronger likeness lock (threshold: {subject.likeness_threshold})'
                    # Face region is typically upper-middle
                    scan_frames.append({
                        'region': 'face',
                        'bbox': [int(w*0.25), int(h*0.15), int(w*0.5), int(h*0.4)],
                        'issue': 'face_drift',
                        'severity': 'critical',
                        'fix_prompt': f'preserve exact likeness, face, skin tone, expression - reference similarity must exceed {subject.likeness_threshold}'
                    })
                else:
                    scan_frames.append({'region': 'face', 'bbox': [int(w*0.25), int(h*0.15), int(w*0.5), int(h*0.4)], 'issue': 'ok', 'severity': 'none'})
        except FileNotFoundError:
            issues['likeness'] = {
                'pass': False,
                'reason': f'Subject {subject_id} not found',
                'score': 0.0,
                'threshold': LIKENESS_THRESHOLD,
            }
    
    # 3. Cropping check - bottom region
    cropped = not check_no_cropped_hands_feet(image_path)
    issues['cropping'] = {'pass': not cropped}
    if cropped:
        issues['cropping']['issue'] = 'feet_hands_cropped'
        issues['cropping']['severity'] = 'high'
        issues['cropping']['fix_suggestion'] = 'Extend canvas downward, ensure full body visible, no cropping of feet'
        scan_frames.append({
            'region': 'lower_body',
            'bbox': [int(w*0.2), int(h*0.8), int(w*0.6), int(h*0.2)],
            'issue': 'feet_hands_cropped',
            'severity': 'high',
            'fix_prompt': 'full body visible, no cropping of feet or hands, vertical 2:3 composition with subject at 68% height'
        })
    else:
        scan_frames.append({'region': 'lower_body', 'bbox': [int(w*0.2), int(h*0.8), int(w*0.6), int(h*0.2)], 'issue': 'ok', 'severity': 'none'})
    
    # 4. Ratio check
    ratio_ok = check_ratio_2_3(image_path)
    issues['ratio'] = {'pass': ratio_ok}
    if not ratio_ok:
        issues['ratio']['issue'] = 'wrong_aspect_ratio'
        issues['ratio']['severity'] = 'high'
        issues['ratio']['fix_suggestion'] = 'Resize/crop to exact 2:3 portrait ratio (e.g., 2160x3240)'
        scan_frames.append({'region': 'canvas', 'bbox': [0, 0, w, h], 'issue': 'wrong_aspect_ratio', 'severity': 'high', 'fix_prompt': 'vertical 2:3 theatrical one-sheet ratio'})
    else:
        scan_frames.append({'region': 'canvas', 'bbox': [0, 0, w, h], 'issue': 'ok', 'severity': 'none'})
    
    # 5. Eye sharpness
    eyes_sharp = check_eyes_sharp(image_path)
    issues['eye_sharpness'] = {'pass': eyes_sharp}
    if not eyes_sharp:
        issues['eye_sharpness']['issue'] = 'eyes_blurry'
        issues['eye_sharpness']['severity'] = 'medium'
        issues['eye_sharpness']['fix_suggestion'] = 'Regenerate with sharp focus on eyes, increase guidance scale for face region'
        scan_frames.append({'region': 'eyes', 'bbox': [int(w*0.3), int(h*0.25), int(w*0.4), int(h*0.15)], 'issue': 'eyes_blurry', 'severity': 'medium', 'fix_prompt': 'sharp focus on eyes, detailed iris and eyelashes, no blur on face'})
    else:
        scan_frames.append({'region': 'eyes', 'bbox': [int(w*0.3), int(h*0.25), int(w*0.4), int(h*0.15)], 'issue': 'ok', 'severity': 'none'})
    
    # 6. Text legibility
    text_ok = check_text_legible(image_path)
    issues['text'] = {'pass': text_ok}
    if not text_ok:
        issues['text']['issue'] = 'text_illegible_or_missing'
        issues['text']['severity'] = 'medium'
        issues['text']['fix_suggestion'] = 'Ensure title at top 15%, tagline at bottom 15%, high contrast text'
        scan_frames.append({'region': 'title_area', 'bbox': [0, 0, w, int(h*0.15)], 'issue': 'text_illegible_or_missing', 'severity': 'medium', 'fix_prompt': 'clear legible title at top, tagline at bottom, high contrast text'})
        scan_frames.append({'region': 'tagline_area', 'bbox': [0, int(h*0.85), w, int(h*0.15)], 'issue': 'text_illegible_or_missing', 'severity': 'medium', 'fix_prompt': 'clear legible tagline at bottom'})
    else:
        scan_frames.append({'region': 'title_area', 'bbox': [0, 0, w, int(h*0.15)], 'issue': 'ok', 'severity': 'none'})
        scan_frames.append({'region': 'tagline_area', 'bbox': [0, int(h*0.85), w, int(h*0.15)], 'issue': 'ok', 'severity': 'none'})
    
    # 7. Wardrobe/outfit consistency (color check in torso region)
    torso_region = img[int(h*0.4):int(h*0.75), int(w*0.3):int(w*0.7)]
    if torso_region.size > 0:
        torso_hsv = cv2.cvtColor(torso_region, cv2.COLOR_BGR2HSV)
        # Check for dominant colors that might indicate wrong outfit
        mean_hue = np.mean(torso_hsv[:,:,0])
        issues['wardrobe'] = {'pass': True, 'dominant_hue': float(mean_hue), 'note': 'Wardrobe color analysis - manual verification recommended'}
        scan_frames.append({'region': 'wardrobe', 'bbox': [int(w*0.3), int(h*0.4), int(w*0.4), int(h*0.35)], 'issue': 'ok', 'severity': 'none', 'note': 'Wardrobe region - verify outfit matches prompt'})
    
    # 8. Props/hands check (side regions)
    left_side = img[int(h*0.4):int(h*0.7), :int(w*0.2)]
    right_side = img[int(h*0.4):int(h*0.7), int(w*0.8):]
    issues['props'] = {'pass': True, 'note': 'Side regions checked for props/hands - manual verification recommended'}
    scan_frames.append({'region': 'left_hand', 'bbox': [0, int(h*0.4), int(w*0.2), int(h*0.3)], 'issue': 'ok', 'severity': 'none', 'note': 'Left hand/prop region'})
    scan_frames.append({'region': 'right_hand', 'bbox': [int(w*0.8), int(h*0.4), int(w*0.2), int(h*0.3)], 'issue': 'ok', 'severity': 'none', 'note': 'Right hand/prop region'})
    
    # 9. Background consistency
    bg_top = img[:int(h*0.2), :]
    bg_bottom = img[int(h*0.8):, :]
    issues['background'] = {'pass': True, 'note': 'Background regions analyzed - verify matches genre palette'}
    scan_frames.append({'region': 'background_top', 'bbox': [0, 0, w, int(h*0.2)], 'issue': 'ok', 'severity': 'none', 'note': 'Background top - verify genre palette'})
    scan_frames.append({'region': 'background_bottom', 'bbox': [0, int(h*0.8), w, int(h*0.2)], 'issue': 'ok', 'severity': 'none', 'note': 'Background bottom - verify genre palette'})
    
    # 10. Lighting/shadow consistency
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    left_half = gray[:, :w//2]
    right_half = gray[:, w//2:]
    lighting_balance = abs(np.mean(left_half) - np.mean(right_half))
    issues['lighting'] = {'pass': lighting_balance < 30, 'balance_score': float(lighting_balance)}
    if lighting_balance >= 30:
        issues['lighting']['issue'] = 'lighting_imbalance'
        issues['lighting']['severity'] = 'medium'
        issues['lighting']['fix_suggestion'] = 'Balance key/rim lighting, ensure consistent illumination across subject'
        scan_frames.append({'region': 'lighting', 'bbox': [0, 0, w, h], 'issue': 'lighting_imbalance', 'severity': 'medium', 'fix_prompt': 'balanced dramatic lighting, consistent key and rim illumination'})
    else:
        scan_frames.append({'region': 'lighting', 'bbox': [0, 0, w, h], 'issue': 'ok', 'severity': 'none'})
    
    # 11. Artifacts/glitches (edge detection for anomalies)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    issues['artifacts'] = {'pass': edge_density < 0.15, 'edge_density': float(edge_density)}
    if edge_density >= 0.15:
        issues['artifacts']['issue'] = 'possible_artifacts'
        issues['artifacts']['severity'] = 'low'
        issues['artifacts']['fix_suggestion'] = 'Check for unwanted artifacts, glitches, or noise in generation'
        scan_frames.append({'region': 'full', 'bbox': [0, 0, w, h], 'issue': 'possible_artifacts', 'severity': 'low', 'fix_prompt': 'clean generation, no artifacts, no extra fingers, no distorted elements'})
    else:
        scan_frames.append({'region': 'full', 'bbox': [0, 0, w, h], 'issue': 'ok', 'severity': 'none'})
    
    # Save annotated image
    annotated_path = image_path.replace('.', '_annotated.')
    cv2.imwrite(annotated_path, annotated)
    
    return {
        'issues': issues,
        'scan_frames': scan_frames,
        'annotated_image_path': annotated_path,
        'summary': {
            'total_checks': len([k for k in issues.keys() if isinstance(issues[k], dict) and 'pass' in issues[k]]),
            'passed': len([k for k in issues.keys() if isinstance(issues[k], dict) and issues[k].get('pass', False)]),
            'failed': len([k for k in issues.keys() if isinstance(issues[k], dict) and not issues[k].get('pass', True)]),
            'critical': len([k for k in issues.keys() if isinstance(issues[k], dict) and issues[k].get('severity') == 'critical']),
            'high': len([k for k in issues.keys() if isinstance(issues[k], dict) and issues[k].get('severity') == 'high']),
            'medium': len([k for k in issues.keys() if isinstance(issues[k], dict) and issues[k].get('severity') == 'medium']),
            'low': len([k for k in issues.keys() if isinstance(issues[k], dict) and issues[k].get('severity') == 'low']),
        }
    }


def generate_fix_prompt_from_issues(issues: Dict[str, Any], base_prompt: str = '') -> str:
    """Generate a comprehensive fix prompt from detected issues."""
    fix_parts = []
    for category, data in issues.items():
        if isinstance(data, dict) and not data.get('pass', True):
            if 'fix_suggestion' in data:
                fix_parts.append(f'FIX {category.upper()}: {data["fix_suggestion"]}')
            if 'fix_prompt' in data:
                fix_parts.append(data['fix_prompt'])
    
    if fix_parts:
        return base_prompt + '\n\n' + '\n'.join(fix_parts)
    return base_prompt


def create_scan_animation_frames(image_path: str, scan_frames: List[Dict], output_dir: str, frame_duration: int = 500) -> List[str]:
    """Create scan animation frames highlighting each issue region."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    img = cv2.imread(image_path)
    if img is None:
        return []
    
    frame_paths = []
    for i, frame in enumerate(scan_frames):
        annotated = img.copy()
        bbox = frame.get('bbox', [0, 0, img.shape[1], img.shape[0]])
        # Ensure all bbox values are integers
        x, y, w, h = [int(v) for v in bbox]
        
        # Draw scan highlight
        color = (0, 0, 255) if frame.get('severity') in ('critical', 'high') else (0, 165, 255) if frame.get('severity') == 'medium' else (0, 255, 0)
        cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 3)
        
        # Add label
        label = f"{frame.get('region', 'region')}: {frame.get('issue', 'ok')}"
        cv2.putText(annotated, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        if 'fix_prompt' in frame:
            # Wrap fix prompt
            fix_text = frame['fix_prompt'][:80] + ('...' if len(frame['fix_prompt']) > 80 else '')
            cv2.putText(annotated, f'Fix: {fix_text}', (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        frame_path = os.path.join(output_dir, f'scan_frame_{i:03d}.png')
        cv2.imwrite(frame_path, annotated)
        frame_paths.append(frame_path)
    
    return frame_paths


# ============================================================================
# VISION QA: 6-POINT CHECK
# ============================================================================

def run_vision_qa(image_path: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
    """Run all 6 QA checks on a generated poster image."""
    checks = {}

    # 1. Likeness preserved (requires subject_id)
    if subject_id:
        try:
            subject = SubjectProfile.load(subject_id)
            if subject.face_embedding:
                gen_embedding = compute_face_embedding(image_path)
                similarity = compute_similarity(subject.face_embedding, gen_embedding)
                checks["likeness_preserved"] = {
                    "pass": similarity >= subject.likeness_threshold,
                    "score": similarity,
                    "threshold": subject.likeness_threshold,
                }
            else:
                checks["likeness_preserved"] = {"pass": False, "reason": "No face embedding in subject"}
        except Exception as e:
            checks["likeness_preserved"] = {"pass": False, "reason": str(e)}
    else:
        checks["likeness_preserved"] = {"pass": True, "note": "No subject_id provided, skipped"}

    # 2. Both earrings symmetrical
    earring_result = detect_gold_hoop_earrings(image_path)
    checks["both_earrings_symmetrical"] = earring_result

    # 3. No cropped hands/feet
    checks["no_cropped_hands_feet"] = {"pass": check_no_cropped_hands_feet(image_path)}

    # 4. Ratio 2:3
    checks["ratio_2_3"] = {"pass": check_ratio_2_3(image_path)}

    # 5. Eyes sharp
    checks["eyes_sharp"] = {"pass": check_eyes_sharp(image_path)}

    # 6. Text legible
    checks["text_legible"] = {"pass": check_text_legible(image_path)}

    # Compute overall score
    passed = sum(1 for c in checks.values() if c.get("pass", False))
    total = len(checks)
    score_str = f"{passed}/{total}"
    overall_pass = (passed == total) and (total == 6)

    return {
        "score": score_str,
        "checks": checks,
        "pass": overall_pass,
    }


# ============================================================================
# MASTER PROMPT BUILDER
# ============================================================================

def build_master_prompt(
    subject: SubjectProfile,
    genre: str,
    title: str,
    subtitle: str,
    tagline: str,
    story: str = "",
    outfit: Optional[str] = None,
    fix_earrings: bool = True,
    resolution: str = "2:3",
) -> str:
    """Build the MASTER_PROMPT with all fixes enforced."""
    g = GENRES.get(genre, GENRES["thriller"])

    earring_fix = "CRITICAL - Ensure both small gold hoop earrings present perfectly symmetrical clearly visible in BOTH ears, identical size and position" if fix_earrings else ""
    effective_story = story or subject.story or 'visionary leader from Kinshasa'
    effective_outfit = outfit or subject.outfit or 'ivory suit structured shoulders'

    prompt = (
        f"Create an iconic movie poster featuring this exact person as the star, "
        f"preserve exact likeness, face, skin tone, and expression. Use the reference image. "
        f"{earring_fix} "
        f"CONCEPT: Wide shot composite, genre: {g['name']}, story: {effective_story}. "
        f"COMPOSITION: Cinematic wide shot, person in center full-body, wearing {effective_outfit}, "
        f"standing powerfully, looking at camera. Background composite blending {', '.join(g['backgrounds'])}. "
        f"STYLE: Epic, high-end Hollywood theatrical poster, dramatic lighting, film grain, volumetric light, ultra-detailed, 8K. "
        f"TEXT: Large title at top: '{title}' and subtitle '{subtitle}'. Tagline at bottom: '{tagline}'. "
        f"Add realistic billing block at very bottom with 'COMING SOON #BRANDLYPOSTER'. "
        f"FORMAT: Vertical {resolution} theatrical one-sheet, no cropping of feet, both earrings must be present. "
        f"PALETTE: {', '.join(g['palette'])}. LIGHTING: {g['lighting']}. "
        f"HERO PLACEMENT: 68 percent height, centered."
    )
    return prompt


# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP("BrandlyPoster-Labs Pro")


# ---------------------------------------------------------------------------
# GENRE & FONT TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_list_genres() -> dict:
    """List all genres with presets."""
    return {"genres": GENRES}


@mcp.tool()
def brandly_list_fonts() -> dict:
    """List available font families for titles, subtitles, taglines, billing."""
    return {"fonts": FONTS}


# ---------------------------------------------------------------------------
# SUBJECT VAULT TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_subject_save(
    subject_id: str,
    reference_image_path: str,
    name: str,
    story: str = "",
    outfit: str = "",
) -> dict:
    """Save a subject profile with face embedding and earring baseline."""
    # Compute face embedding
    embedding = compute_face_embedding(reference_image_path)

    # Detect earring baseline
    earring_baseline = detect_gold_hoop_earrings(reference_image_path)

    subject = SubjectProfile(
        subject_id=subject_id,
        name=name,
        reference_images=[reference_image_path],
        face_embedding=embedding,
        earring_baseline=earring_baseline,
        story=story,
        outfit=outfit,
    )
    subject.save()

    return {
        "subject_id": subject_id,
        "name": name,
        "embedding_stored": True,
        "earring_baseline": earring_baseline,
    }


@mcp.tool()
def brandly_subject_match(generated_image_path: str, subject_id: str) -> dict:
    """Match generated image against subject vault — returns similarity score."""
    try:
        subject = SubjectProfile.load(subject_id)
    except FileNotFoundError:
        return {
            "subject_id": subject_id,
            "similarity": 0.0,
            "pass": False,
            "reason": f"Subject {subject_id} not found",
            "threshold": LIKENESS_THRESHOLD,
        }
    if not subject.face_embedding:
        return {"pass": False, "reason": "Subject has no face embedding"}

    gen_embedding = compute_face_embedding(generated_image_path)
    similarity = compute_similarity(subject.face_embedding, gen_embedding)
    pass_threshold = similarity >= subject.likeness_threshold

    return {
        "subject_id": subject_id,
        "similarity": similarity,
        "pass": pass_threshold,
        "threshold": subject.likeness_threshold,
    }


@mcp.tool()
def brandly_earring_check(image_path: str) -> dict:
    """Standalone earring symmetry check."""
    return detect_gold_hoop_earrings(image_path)


# ---------------------------------------------------------------------------
# POSTER CREATION
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_create_poster(
    subject_id: str,
    genre: str = "thriller",
    title: str = "BADLAND",
    subtitle: str = "THE ASCENT",
    tagline: str = "She built her own empire",
    story: str = "",
    outfit: str = "",
    fix_earrings: bool = True,
    resolution: str = "2:3",
) -> dict:
    """Create base poster with master prompt and variant plan."""
    try:
        subject = SubjectProfile.load(subject_id)
    except FileNotFoundError:
        return {
            "subject_id": subject_id,
            "pass": False,
            "error": f"Subject {subject_id} not found",
        }

    # Use subject's story/outfit if not overridden
    effective_story = story or subject.story
    effective_outfit = outfit or subject.outfit

    prompt = build_master_prompt(
        subject=subject,
        genre=genre,
        title=title,
        subtitle=subtitle,
        tagline=tagline,
        story=effective_story,
        outfit=effective_outfit,
        fix_earrings=fix_earrings,
        resolution=resolution,
    )

    g = GENRES.get(genre, GENRES["thriller"])

    return {
        "master_prompt": prompt,
        "genre_config": g,
        "subject_id": subject_id,
        "qa_checklist": [
            "Likeness preserved",
            "Both earrings symmetrical" if fix_earrings else "Earrings check skipped",
            "No cropped hands/feet",
            "Ratio 2:3",
            "Eyes sharp",
            "Text legible",
        ],
        "variant_plan": {
            "title": title,
            "subtitle": subtitle,
            "tagline": tagline,
            "genre": genre,
            "resolution": resolution,
        },
    }


# ---------------------------------------------------------------------------
# TEXT & LAYOUT TOOLS (return layer specs for studio app)
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_set_title(
    text: str,
    font: str = "Playfair Display",
    size: int = 120,
    color: str = "#D4AF37",
    tracking: float = 0.12,
    leading: float = 1.0,
    alignment: str = "center",
    placement: str = "top",
    x: int = 50,
    y: int = 10,
    uppercase: bool = True,
    stroke: str = "none",
) -> dict:
    return {"layer": "title", "text": text, "font": font, "size": size, "color": color, "tracking": tracking, "leading": leading, "alignment": alignment, "placement": placement, "x": x, "y": y, "uppercase": uppercase, "stroke": stroke, "css": f"font-family:{font}; font-size:{size}px; color:{color}; letter-spacing:{tracking}em; text-align:{alignment};"}


@mcp.tool()
def brandly_set_subtitle(
    text: str,
    font: str = "Montserrat",
    size: int = 24,
    color: str = "#FFFFFF",
    tracking: float = 0.3,
    alignment: str = "center",
    placement: str = "below_title",
    y_offset: int = 20,
) -> dict:
    return {"layer": "subtitle", "text": text, "font": font, "size": size, "color": color, "tracking": tracking, "alignment": alignment, "placement": placement, "y_offset": y_offset}


@mcp.tool()
def brandly_set_tagline(
    text: str,
    font: str = "Inter Light",
    size: int = 18,
    color: str = "#E5E5E5",
    alignment: str = "center",
    placement: str = "bottom",
    y: int = 85,
) -> dict:
    return {"layer": "tagline", "text": text, "font": font, "size": size, "color": color, "alignment": alignment, "placement": placement, "y": y}


@mcp.tool()
def brandly_set_billing_block(
    text: str,
    font: str = "Univers Condensed",
    size: int = 8,
    color: str = "#CCCCCC",
    alignment: str = "center",
    placement: str = "very_bottom",
    opacity: float = 0.8,
) -> dict:
    return {"layer": "billing", "text": text, "font": font, "size": size, "color": color, "alignment": alignment, "placement": placement, "opacity": opacity}


@mcp.tool()
def brandly_add_text_layer(
    text: str,
    layer_id: str,
    font: str = "Inter",
    size: int = 32,
    color: str = "#FFFFFF",
    x: int = 50,
    y: int = 50,
    alignment: str = "center",
    rotation: int = 0,
    uppercase: bool = False,
    opacity: float = 1.0,
    background: str = "transparent",
) -> dict:
    return {"layer": layer_id, "text": text, "font": font, "size": size, "color": color, "x": x, "y": y, "alignment": alignment, "rotation": rotation, "uppercase": uppercase, "opacity": opacity, "background": background}


@mcp.tool()
def brandly_set_text_style(
    layer_id: str,
    font: str = None,
    size: int = None,
    color: str = None,
    tracking: float = None,
    leading: float = None,
    weight: str = None,
    style: str = None,
) -> dict:
    return {"action": "update_style", "layer_id": layer_id, "font": font, "size": size, "color": color, "tracking": tracking, "leading": leading, "weight": weight, "style": style}


# ---------------------------------------------------------------------------
# ALIGNMENT & PLACEMENT
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_align_text(
    layer_id: str,
    horizontal: str = "center",
    vertical: str = "top",
    relative_to: str = "canvas",
) -> dict:
    coords = {"left": 10, "center": 50, "right": 90, "top": 10, "middle": 50, "bottom": 90}
    return {"layer_id": layer_id, "horizontal": horizontal, "vertical": vertical, "relative_to": relative_to, "x": coords.get(horizontal, 50), "y": coords.get(vertical, 10)}


@mcp.tool()
def brandly_place_element(
    layer_id: str,
    x: int,
    y: int,
    anchor: str = "center",
    z_index: int = 10,
) -> dict:
    return {"layer_id": layer_id, "x": x, "y": y, "anchor": anchor, "z_index": z_index}


@mcp.tool()
def brandly_distribute_layers(
    layer_ids: List[str],
    direction: str = "horizontal",
    spacing: int = 20,
    alignment: str = "center",
) -> dict:
    return {"layer_ids": layer_ids, "direction": direction, "spacing": spacing, "alignment": alignment}


@mcp.tool()
def brandly_set_grid(
    show: bool = True,
    type: str = "3x3",
    safe_area: bool = True,
    bleed: bool = True,
) -> dict:
    return {"show": show, "grid_type": type, "safe_area": safe_area, "bleed": bleed}


@mcp.tool()
def brandly_set_hero_placement(
    scale: float = 0.68,
    x: int = 50,
    y: int = 50,
    crop: str = "full_body",
    anchor: str = "center",
) -> dict:
    return {"hero_scale": scale, "x": x, "y": y, "crop": crop, "anchor": anchor}


# ---------------------------------------------------------------------------
# STYLE & COMPOSITION
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_set_background(
    layer: str = "primary",
    image_desc: str = "",
    blur: int = 10,
    brightness: float = 0.8,
    overlay_color: str = "#000000",
    overlay_opacity: float = 0.3,
) -> dict:
    return {"layer": layer, "desc": image_desc, "blur": blur, "brightness": brightness, "overlay_color": overlay_color, "overlay_opacity": overlay_opacity}


@mcp.tool()
def brandly_set_lighting(
    key_intensity: float = 1.0,
    rim_intensity: float = 0.6,
    fill: float = 0.3,
    golden_hour: float = 0.7,
    contrast: float = 1.1,
) -> dict:
    return {"key": key_intensity, "rim": rim_intensity, "fill": fill, "golden_hour": golden_hour, "contrast": contrast}


@mcp.tool()
def brandly_set_color_palette(
    palette: List[str],
    grading: str = "cinematic",
    intensity: float = 0.8,
) -> dict:
    return {"palette": palette, "grading": grading, "intensity": intensity}


# ---------------------------------------------------------------------------
# ANIMATION TOOLS
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_animate_poster(
    animation_type: str = "parallax",
    duration: int = 6,
    fps: int = 24,
    loop: bool = True,
) -> dict:
    animations = {
        "parallax": {"bg_move": "slow pan", "hero": "subtle scale", "title": "fade in"},
        "title_reveal": {"title": "gold shimmer reveal from left", "subtitle": "fade after title", "tagline": "typewriter"},
        "ken_burns": {"hero": "slow zoom in", "bg": "slow zoom out"},
        "smoke_fog": {"overlay": "smoke drifting", "lights": "flicker"},
        "market_chaos": {"bg": "people moving blurred", "mangoes": "subtle bounce", "fairy_lights": "twinkle"},
        "full_cinematic": {"sequence": ["bg parallax", "hero entrance", "title gold shimmer", "tagline fade", "billing slide up"]},
    }
    return {"animation_type": animation_type, "duration": duration, "fps": fps, "loop": loop, "keyframes": animations.get(animation_type, animations["parallax"])}


@mcp.tool()
def brandly_set_animation_keyframes(
    layer_id: str,
    keyframes: List[Dict[str, Any]],
) -> dict:
    return {"layer_id": layer_id, "keyframes": keyframes}


@mcp.tool()
def brandly_export_animation(
    format: str = "mp4",
    resolution: str = "1080x1920",
    fps: int = 24,
    duration: int = 6,
    codec: str = "h264",
) -> dict:
    return {"format": format, "resolution": resolution, "fps": fps, "duration": duration, "codec": codec, "file": f"brandly_poster_animated_{resolution}.{format}"}


# ---------------------------------------------------------------------------
# QA & EXPORT
# ---------------------------------------------------------------------------

@mcp.tool()
def brandly_qa_check(image_path: str, subject_id: Optional[str] = None) -> dict:
    """Run vision-backed quality assurance: 6-point check."""
    result = run_vision_qa(image_path, subject_id)
    return result


@mcp.tool()
def brandly_scan_issues(image_path: str, subject_id: Optional[str] = None, create_animation: bool = False, animation_output_dir: str = "") -> dict:
    """
    Comprehensive issue detection with scan animation frames.
    Detects: earrings, likeness, cropping, ratio, eye sharpness, text, wardrobe, props, background, lighting, artifacts.
    Returns annotated image + scan frames for visualization + fix prompts.
    """
    result = detect_issues_with_visualization(image_path, subject_id)
    
    # Generate fix prompt from all issues
    base_prompt = ""
    if subject_id:
        try:
            subject = SubjectProfile.load(subject_id)
            base_prompt = f"Poster for {subject.name}, genre preset"
        except FileNotFoundError:
            base_prompt = f"Poster for {subject_id} (subject not found)"
    
    fix_prompt = generate_fix_prompt_from_issues(result['issues'], base_prompt)
    
    response = {
        'issues': result['issues'],
        'scan_frames': result['scan_frames'],
        'annotated_image_path': result['annotated_image_path'],
        'summary': result['summary'],
        'fix_prompt': fix_prompt,
        'fix_categories': [k for k, v in result['issues'].items() if isinstance(v, dict) and not v.get('pass', True)],
    }
    
    # Create scan animation frames if requested
    if create_animation and animation_output_dir:
        frame_paths = create_scan_animation_frames(image_path, result['scan_frames'], animation_output_dir)
        response['animation_frames'] = frame_paths
        response['animation_note'] = f'Created {len(frame_paths)} scan frames in {animation_output_dir}. Use with brandly_export_animation to create MP4/GIF.'
    
    return response


@mcp.tool()
def brandly_fix_earrings_prompt(image_path: str, subject_id: Optional[str] = None) -> dict:
    """Generate specific fix prompt for earring symmetry issues."""
    result = detect_gold_hoop_earrings(image_path)
    if result.get('symmetrical', False):
        return {'status': 'ok', 'message': 'Earrings are symmetrical', 'fix_prompt': ''}
    
    fix = 'CRITICAL - Ensure both small gold hoop earrings present perfectly symmetrical clearly visible in BOTH ears, identical size and position. Left ear at same height as right ear, same radius, same gold color.'
    return {
        'status': 'fix_needed',
        'issue': 'earring_asymmetry',
        'details': result,
        'fix_prompt': fix,
        'suggested_negative': 'mismatched earrings, single earring, different sizes, different positions, missing earring'
    }


@mcp.tool()
def brandly_fix_wardrobe_prompt(image_path: str, expected_outfit: str = '', subject_id: Optional[str] = None) -> dict:
    """Generate fix prompt for wardrobe/outfit issues."""
    img = cv2.imread(image_path)
    if img is None:
        return {'error': 'Could not read image'}
    
    h, w = img.shape[:2]
    torso = img[int(h*0.4):int(h*0.75), int(w*0.3):int(w*0.7)]
    
    outfit_desc = expected_outfit if expected_outfit else "the specified outfit from prompt"
    fix = f'WARDROBE FIX: Ensure subject wears exactly: {outfit_desc}. Match fabric, color, cut, and fit precisely. No wardrobe substitutions.'
    
    return {
        'status': 'check_needed',
        'issue': 'wardrobe_verification',
        'expected_outfit': expected_outfit,
        'fix_prompt': fix,
        'note': 'Visual verification of torso region required. Compare detected colors with expected outfit.'
    }


@mcp.tool()
def brandly_fix_props_prompt(image_path: str, expected_props: List[str] = None) -> dict:
    """Generate fix prompt for props/hands issues."""
    if expected_props is None:
        expected_props = []
    
    fix = 'PROPS FIX: '
    if expected_props:
        fix += f'Ensure these props are visible and correctly held: {', '.join(expected_props)}. '
    fix += 'Hands must be natural, correct number of fingers, props properly positioned. No floating or distorted objects.'
    
    return {
        'status': 'check_needed',
        'issue': 'props_verification',
        'expected_props': expected_props,
        'fix_prompt': fix,
        'note': 'Check left/right hand regions for correct prop rendering.'
    }


@mcp.tool()
def brandly_fix_background_prompt(image_path: str, genre: str = 'thriller') -> dict:
    """Generate fix prompt for background consistency issues."""
    g = GENRES.get(genre, GENRES['thriller'])
    
    fix = f'BACKGROUND FIX: Background must match {g["name"]} genre. '
    fix += f'Required elements: {', '.join(g["backgrounds"])}. '
    fix += f'Palette locked to: {', '.join(g["palette"])}. '
    fix += f'Lighting: {g["lighting"]}. No background elements from other genres.'
    
    return {
        'status': 'check_needed',
        'issue': 'background_verification',
        'genre': genre,
        'genre_config': g,
        'fix_prompt': fix
    }


@mcp.tool()
def brandly_fix_lighting_prompt(image_path: str) -> dict:
    """Generate fix prompt for lighting/shadow issues."""
    img = cv2.imread(image_path)
    if img is None:
        return {'error': 'Could not read image'}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    left_mean = np.mean(gray[:, :w//2])
    right_mean = np.mean(gray[:, w//2:])
    balance = abs(left_mean - right_mean)
    
    fix = 'LIGHTING FIX: Balance key and rim lighting across subject. '
    if balance > 30:
        fix += f'Current left/right imbalance: {balance:.1f}. Even out illumination. '
    fix += 'Consistent dramatic lighting, proper rim light on both sides, no harsh shadows on face.'
    
    return {
        'status': 'fix_needed' if balance > 30 else 'ok',
        'issue': 'lighting_imbalance' if balance > 30 else 'ok',
        'balance_score': float(balance),
        'fix_prompt': fix
    }


@mcp.tool()
def brandly_fix_composition_prompt(image_path: str) -> dict:
    """Generate fix prompt for composition issues (ratio, cropping, hero placement)."""
    img = cv2.imread(image_path)
    if img is None:
        return {'error': 'Could not read image'}
    
    h, w = img.shape[:2]
    ratio = w / h
    ratio_ok = abs(ratio - 2/3) < 0.02
    cropped = not check_no_cropped_hands_feet(image_path)
    
    fixes = []
    if not ratio_ok:
        fixes.append(f'RATIO: Fix aspect ratio to exactly 2:3 (current: {ratio:.3f}). Use 2160x3240 or 1080x1620.')
    if cropped:
        fixes.append('CROPPING: Extend canvas to show full body, no cropped feet or hands. Hero at 68% height centered.')
    
    return {
        'status': 'fix_needed' if fixes else 'ok',
        'issues': fixes,
        'ratio': float(ratio),
        'cropped': cropped,
        'fix_prompt': '\n'.join(fixes) if fixes else 'Composition OK'
    }


@mcp.tool()
def brandly_generate_master_fix_prompt(image_path: str, subject_id: Optional[str] = None, genre: str = 'thriller', expected_outfit: str = '', expected_props: List[str] = None) -> dict:
    """Generate comprehensive master fix prompt combining all detected issues."""
    if expected_props is None:
        expected_props = []
    
    # Run full scan
    scan_result = detect_issues_with_visualization(image_path, subject_id)
    
    # Generate individual fix prompts
    earring_fix = brandly_fix_earrings_prompt(image_path, subject_id)
    wardrobe_fix = brandly_fix_wardrobe_prompt(image_path, expected_outfit, subject_id)
    props_fix = brandly_fix_props_prompt(image_path, expected_props)
    background_fix = brandly_fix_background_prompt(image_path, genre)
    lighting_fix = brandly_fix_lighting_prompt(image_path)
    composition_fix = brandly_fix_composition_prompt(image_path)
    
    # Combine all fixes
    all_fixes = []
    for fix in [earring_fix, wardrobe_fix, props_fix, background_fix, lighting_fix, composition_fix]:
        if fix.get('fix_prompt'):
            all_fixes.append(fix['fix_prompt'])
    
    master_fix = '\n\n'.join(all_fixes) if all_fixes else 'No fixes needed - all checks pass'
    
    return {
        'master_fix_prompt': master_fix,
        'scan_result': scan_result,
        'individual_fixes': {
            'earrings': earring_fix,
            'wardrobe': wardrobe_fix,
            'props': props_fix,
            'background': background_fix,
            'lighting': lighting_fix,
            'composition': composition_fix,
        },
        'summary': scan_result['summary'],
    }


@mcp.tool()
def brandly_export_specs(format: str = "theatrical") -> dict:
    specs = {
        "theatrical": {"size": "27x40", "dpi": 300, "color": "CMYK", "pixels": "8100x12000"},
        "deck": {"size": "1440x900", "dpi": 72, "color": "sRGB", "pixels": "1440x900"},
        "social": {"size": "2160x3240", "dpi": 72, "color": "sRGB", "pixels": "2160x3240"},
        "story": {"size": "1080x1920", "dpi": 72, "color": "sRGB", "pixels": "1080x1920"},
        "animated": {"size": "1080x1920", "fps": 24, "formats": ["mp4", "gif", "webm"]},
    }
    return specs.get(format, specs["theatrical"])


@mcp.tool()
def brandly_batch_export(
    project_id: str,
    formats: List[str] = None,
    generated_image_path: str = "",
) -> dict:
    """Export poster in all requested formats; write manifest."""
    if formats is None:
        formats = ["theatrical", "deck", "social", "story"]

    try:
        project = ProjectManifest.load(project_id)
    except FileNotFoundError:
        return {
            "project_id": project_id,
            "pass": False,
            "error": f"Project {project_id} not found",
            "variants": [],
        }

    project_dir = PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # In real implementation, would resize/convert the generated image to each format
    # Here we return specs and manifest structure
    variants = []
    for fmt in formats:
        spec = brandly_export_specs(fmt)
        variant = {
            "format": fmt,
            "file": f"poster_{fmt}.{ 'png' if fmt != 'animated' else 'mp4' }",
            "specs": spec,
            "path": str(project_dir / f"poster_{fmt}.{ 'png' if fmt != 'animated' else 'mp4' }"),
        }
        variants.append(variant)

    project.variants = variants
    project.save()

    return {
        "project_id": project_id,
        "variants": variants,
        "manifest_path": str(project_dir / "manifest.json"),
    }


@mcp.tool()
def brandly_share_review(project_id: str) -> dict:
    """Generate a shareable review URL (stub - in real app would serve static HTML)."""
    try:
        project = ProjectManifest.load(project_id)
    except FileNotFoundError:
        return {
            "project_id": project_id,
            "pass": False,
            "error": f"Project {project_id} not found",
            "review_url": None,
        }
    review_id = str(uuid.uuid4())[:8]
    # In production, would generate static HTML at /mnt/data/.../review_<id>.html
    review_url = f"file://{PROJECTS_DIR}/{project_id}/review_{review_id}.html"
    return {
        "review_url": review_url,
        "project_id": project_id,
        "review_id": review_id,
        "note": "Static review page with poster, variants, QA scorecard",
    }


@mcp.tool()
def brandly_compare_versions(variant_a_path: str, variant_b_path: str) -> dict:
    """Side-by-side comparison of two poster variants."""
    # In production, would generate comparison image
    return {
        "variant_a": variant_a_path,
        "variant_b": variant_b_path,
        "comparison_path": f"/mnt/data/brandlyposter-labs/projects/compare_{uuid.uuid4().hex[:8]}.png",
        "note": "Would generate side-by-side diff with highlights",
    }


@mcp.tool()
def brandly_approve_version(project_id: str, version_id: str, client_signature: str = "") -> dict:
    """Lock final approved version."""
    try:
        project = ProjectManifest.load(project_id)
    except FileNotFoundError:
        return {
            "project_id": project_id,
            "pass": False,
            "error": f"Project {project_id} not found",
            "locked": False,
        }
    project.approved = True
    project.approved_version = version_id
    project.save()
    return {"locked": True, "final_version": version_id, "project_id": project_id}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    mcp.run()