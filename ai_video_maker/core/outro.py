"""Short, reusable CTA planning and local artwork for the main character."""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .config import ASSETS_DIR, CHARACTER_PATH, DEFAULT_OUTRO_STYLE

STYLES = {
    "creator_desk_mic": ("a tidy creator desk with one microphone", "seated at the desk, smiling gently toward the viewer"),
    "monitor_play_button": ("a neat workspace with one monitor showing a simple play triangle", "beside the monitor, giving a small welcoming gesture"),
    "whiteboard_presenter": ("a simple presentation board in a bright room", "standing beside the board, gesturing toward the viewer"),
    "cozy_creator_room": ("a quiet creator room corner with one chair and one lamp", "waving naturally to the viewer"),
}
REFERENCE_OUTROS = {
    "creator_desk_mic": "see_you_studio.png",
    "monitor_play_button": "thanks_workspace.png",
    "whiteboard_presenter": "whiteboard_like_subscribe.png",
    "cozy_creator_room": "see_you_studio.png",
}


def outro_asset_path(style: str) -> Path | None:
    filename = REFERENCE_OUTROS.get(style)
    path = ASSETS_DIR / "outro" / filename if filename else None
    if path and path.is_file():
        return path
    fallback = ASSETS_DIR / "outro" / "thanks_workspace.png"
    return fallback if fallback.is_file() else None


def choose_style(topic: str, preferred: str | None = None, fixed: bool = False) -> str:
    preferred = preferred if preferred in STYLES else (DEFAULT_OUTRO_STYLE if DEFAULT_OUTRO_STYLE in STYLES else "creator_desk_mic")
    if fixed:
        return preferred
    value = topic.lower()
    if re.search(r"\b(?:computer|ram|ai|technology|software)\b", value):
        return "monitor_play_button"
    if re.search(r"\b(?:study|studying|student|students|learn|learning|education)\b", value):
        return "whiteboard_presenter"
    if re.search(r"\b(?:habit|habits|routine|life|psychology)\b", value):
        return "cozy_creator_room"
    return preferred


def normalize_outro(raw: dict | None, topic: str, takeaway: str = "",
                    preferred_style: str | None = None, fixed: bool = False) -> dict:
    """Keep AI output short and complete; never read unsupported prose aloud."""
    raw = raw if isinstance(raw, dict) else {}
    style = choose_style(topic, preferred_style if fixed else (preferred_style or raw.get("visual_style")), fixed)
    spoken = " ".join(str(raw.get("spoken_text") or "").split()).strip()
    if not spoken or len(spoken.split()) < 8 or len(spoken.split()) > 32:
        lower = topic.lower()
        if re.search(r"\b(?:ram|computer|technology|software|science|explainer)\b", lower):
            spoken = "If this breakdown was useful, subscribe for more simple explainers."
        elif re.search(r"\b(?:habit|habits|routine|productivity|focus|psychology|dopamine)\b", lower):
            spoken = "If this helped you see the pattern, like and subscribe for more."
        else:
            spoken = "If this video helped, leave a like and subscribe for more."
    spoken = re.split(r"(?<=[.!?])\s+", spoken, maxsplit=2)
    spoken = " ".join(spoken[:2]).strip()
    subtitle = " ".join(str(raw.get("subtitle_text") or "Like and subscribe for more").split())[:70]
    try:
        duration = int(raw.get("duration_sec", 5))
    except (TypeError, ValueError):
        duration = 5
    return {
        "cta_angle": str(raw.get("cta_angle") or "helpful_explainer")[:60],
        "spoken_text": spoken,
        "subtitle_text": subtitle,
        "visual_style": style,
        "duration_sec": max(4, min(8, duration)),
        "template": "studio_cta" if fixed else "dynamic_cta",
        "topic": topic,
        "takeaway": takeaway,
    }


def build_outro_prompt(brief: dict) -> str:
    style = brief.get("visual_style", DEFAULT_OUTRO_STYLE)
    place, action = STYLES.get(style, STYLES[DEFAULT_OUTRO_STYLE])
    return (
        "Create a 16:9 clean 2D cartoon end card using the supplied main character reference. "
        "Preserve exactly the character's face, short black hair, pale mint-green shirt, dark pants, "
        "and thin dark outline style. One character only. "
        f"Scene: {place}; the character is {action}. "
        "Warm cream background, restrained mint and brown accents, simple readable pose, friendly closing mood. "
        "Use only two or three meaningful room objects. Keep one side comfortably open for video end-screen elements. "
        "No written words, floating labels, logos, extra people, decorative circles, watermark, or clutter."
    )


def plan_outro_scene(brief: dict) -> dict:
    style = brief["visual_style"]
    asset = outro_asset_path(style)
    return {
        "scene_mode": "outro_cta", "image_strategy": "reference_asset" if asset else "full_scene_ai_or_local",
        "visual_style": style, "visual_prompt": build_outro_prompt(brief),
        "reference_asset": str(asset.relative_to(ASSETS_DIR)) if asset else None,
        "character_visible": True, "character_role": "host", "emotion": "friendly",
        "gesture": "wave" if style == "cozy_creator_room" else "present",
        "character_action": "wave" if style == "cozy_creator_room" else "present",
        "interaction_target": "viewer", "template": brief["template"],
    }


def _font(size: int):
    for path in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_local_outro(brief: dict, output_path: Path) -> None:
    """Use the user's approved image; retain the old local drawing as fallback."""
    asset = outro_asset_path(brief.get("visual_style", ""))
    if asset:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asset, output_path)
        return
    image = Image.new("RGBA", (1920, 1080), (251, 247, 237, 255))
    draw = ImageDraw.Draw(image)
    ink = (55, 56, 55)
    mint = (211, 231, 218)
    brown = (192, 159, 126)
    draw.rectangle((0, 820, 1920, 1080), fill=(241, 233, 217))
    draw.line((0, 820, 1920, 820), fill=ink, width=5)
    style = brief.get("visual_style")
    if style == "whiteboard_presenter":
        draw.rounded_rectangle((1030, 205, 1760, 730), radius=20, fill="white", outline=ink, width=10)
        draw.polygon([(1350, 365), (1350, 555), (1515, 460)], fill=mint, outline=ink)
    elif style == "monitor_play_button":
        draw.rounded_rectangle((1080, 280, 1760, 730), radius=24, fill=(239, 246, 240), outline=ink, width=12)
        draw.polygon([(1325, 375), (1325, 610), (1530, 492)], fill=mint, outline=ink)
        draw.line((1415, 730, 1415, 795), fill=ink, width=14)
    elif style == "creator_desk_mic":
        draw.rounded_rectangle((470, 430, 1040, 835), radius=45, fill=(247, 238, 220), outline=ink, width=8)
    else:
        draw.rounded_rectangle((1160, 465, 1710, 800), radius=32, fill=(255, 249, 236), outline=ink, width=9)
        draw.ellipse((1490, 320, 1625, 455), fill=(244, 220, 151), outline=ink, width=8)
        draw.line((1557, 455, 1557, 625), fill=ink, width=10)
    pose = CHARACTER_PATH.parent / "poses" / "sitting.png" if style == "creator_desk_mic" else CHARACTER_PATH
    if pose.is_file():
        with Image.open(pose) as source:
            character = source.convert("RGBA")
            character.thumbnail((840, 900), Image.Resampling.LANCZOS)
            x = 510 if style == "creator_desk_mic" else 170
            image.alpha_composite(character, (x, 825 - character.height))
    else:
        draw.text((250, 510), "CREATOR", font=_font(80), fill=ink)
    if style == "creator_desk_mic":
        draw.rounded_rectangle((425, 555, 1450, 625), radius=15, fill=brown, outline=ink, width=9)
        draw.line((510, 625, 510, 985), fill=ink, width=12)
        draw.line((1380, 625, 1380, 985), fill=ink, width=12)
        draw.rounded_rectangle((1140, 365, 1210, 495), radius=35, fill=mint, outline=ink, width=9)
        draw.line((1175, 495, 1175, 555), fill=ink, width=10)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(output_path)
