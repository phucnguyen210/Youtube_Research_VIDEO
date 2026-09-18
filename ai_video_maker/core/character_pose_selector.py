"""Resolve acting directions to optional pose assets and a safe master fallback."""
import logging
from pathlib import Path
from .config import ASSETS_DIR, CHARACTER_PATH

LOGGER = logging.getLogger(__name__)
POSE_NAMES = ("idle", "curious", "surprised", "thinking", "explaining", "point_left", "point_right",
              "compare", "warning", "confident", "happy", "questioning", "sitting", "stretching", "working")

POSES = {
    "question_reveal": ["questioning", "curious", "surprised"],
    "cause_effect": ["explaining", "point_right", "point_left"],
    "comparison": ["compare"],
    "consequence": ["warning", "concerned"],
    "takeaway": ["confident", "explaining"],
    "example": ["explaining", "point_right"],
}


def requested_pose(emotion: str, action: str = "none", archetype: str = "example") -> str:
    aliases = {"present":"explaining", "point_at_focus":"point_right", "compare_sides":"compare",
               "warn":"warning", "think":"thinking", "react":"surprised", "celebrate":"happy"}
    if action in {"point_at_focus", "compare_sides", "warn", "think"}:
        return aliases[action]
    if emotion == "concerned":
        return "warning"
    if emotion in POSE_NAMES and emotion != "neutral":
        return emotion
    if action in aliases:
        return aliases[action]
    return POSES.get(archetype, ["idle"])[0]


def select_pose(emotion: str, action: str = "none", archetype: str = "example",
                character_pose: str | None = None) -> tuple[Path, bool]:
    name = character_pose or requested_pose(emotion, action, archetype)
    if name not in POSE_NAMES:
        name = "idle"
    folder = ASSETS_DIR / "character" / "poses"
    candidate = folder / f"{name}.png"
    if candidate.is_file():
        return candidate, True
    LOGGER.warning("Pose '%s' missing - falling back to main character", name)
    return CHARACTER_PATH, False


def pose_status() -> list[dict]:
    folder = ASSETS_DIR / "character" / "poses"
    return [{"name": name, "exists": (folder / f"{name}.png").is_file()} for name in POSE_NAMES]


def pose_prompt(body_pose: str, expression: str, body_language: str) -> str:
    return ("Create a clean 2D full-body pose asset of the exact same cartoon character as the reference. "
            "Preserve hairstyle, face identity, skin tone, clothing, shoes, outline style, proportions, age and palette. "
            f"Body pose: {body_pose}. Facial expression: {expression}. Body language: {body_language}. "
            "Transparent background, centered, no environment or props, expression readable at small size. "
            "Do not redesign the character.")
