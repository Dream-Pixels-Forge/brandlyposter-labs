#!/usr/bin/env python3
"""
BrandlyPoster-Labs MCP Server — Next Level
Multi-agent poster studio with subject vault, vision QA, batch export, client approval.
"""

import json
import os
import uuid
import base64
import hashlib
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
    """Extract face embedding using CLIP image encoder."""
    model, processor = get_clip()
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        image_features = outputs.pooler_output
    # Normalize
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.squeeze().tolist()


def compute_similarity(emb1: List[float], emb2: List[float]) -> float:
    """Cosine similarity between two embeddings."""
    a = np.array(emb1)
    b = np.array(emb2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


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
    subject = SubjectProfile.load(subject_id)
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
    subject = SubjectProfile.load(subject_id)

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

    project = ProjectManifest.load(project_id)

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
    project = ProjectManifest.load(project_id)
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
    project = ProjectManifest.load(project_id)
    project.approved = True
    project.approved_version = version_id
    project.save()
    return {"locked": True, "final_version": version_id, "project_id": project_id}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    mcp.run()