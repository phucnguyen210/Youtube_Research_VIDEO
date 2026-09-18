"""Generate optional transparent character pose assets from the master reference."""
from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image

from .character_pose_selector import POSE_NAMES
from .config import ASSETS_DIR, CHARACTER_PATH, OPENAI_API_KEY

POSE_DIRECTIONS = {
    "idle": ("gentle smile and relaxed eyes", "standing naturally, arms at sides"),
    "curious": ("raised brows and inquisitive eyes", "leaning toward an unseen subject, one palm open"),
    "surprised": ("wide eyes, raised brows and open mouth", "leaning back, one hand near chest, other open"),
    "thinking": ("focused eyes and thoughtful mouth", "one hand on chin, slight forward lean"),
    "explaining": ("friendly confident smile", "one arm extended with open palm"),
    "point_left": ("engaged expression, looking left", "arm clearly pointing left"),
    "point_right": ("engaged expression, looking right", "arm clearly pointing right"),
    "compare": ("attentive eyes looking between two sides", "both arms extended left and right"),
    "warning": ("concerned brows and serious mouth", "one palm raised in a wait gesture"),
    "confident": ("relaxed confident smile", "upright posture and presenting gesture"),
    "happy": ("wide cheerful smile", "open celebratory posture"),
    "questioning": ("raised brows and slightly puzzled face", "one hand lifted in a question gesture"),
    "sitting": ("calm attentive expression", "sitting naturally, full body visible"),
    "stretching": ("awake relaxed smile", "both arms stretching overhead"),
    "working": ("focused eyes and concentrated mouth", "sitting and working at an invisible desk, hands posed for work"),
}


def pose_prompt(name: str) -> str:
    expression, action = POSE_DIRECTIONS[name]
    return ("Create a clean full-body 2D illustration of the EXACT SAME cartoon character in the reference image. "
            "Preserve hairstyle, face identity, skin tone, shirt, pants, shoes, body proportions, outline thickness, "
            "illustration style, color palette and age. Change ONLY facial expression, arms, posture and gaze. "
            f"Pose: {name}. Facial expression: {expression}. Body action: {action}. "
            "This is a standalone character pose asset. Center the entire figure. Genuine transparent background. "
            "No environment, decorative background, props, text, additional person or redesign. "
            "Make the expression readable when small in a 16:9 video scene.")


def generate_pose(name: str, overwrite: bool = False, client=None) -> Path:
    if name not in POSE_NAMES:
        raise ValueError("Unknown pose")
    output = ASSETS_DIR / "character" / "poses" / f"{name}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        return output
    if not OPENAI_API_KEY and client is None:
        raise RuntimeError("OPENAI_API_KEY is required to generate poses")
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    with CHARACTER_PATH.open("rb") as reference:
        response = client.images.edit(
            model="gpt-image-1", image=reference, prompt=pose_prompt(name),
            background="transparent", output_format="png", size="1024x1024", quality="high",
        )
    data = base64.b64decode(response.data[0].b64_json)
    temporary = output.with_suffix(".tmp.png")
    temporary.write_bytes(data)
    try:
        with Image.open(temporary) as image:
            if image.mode != "RGBA" or image.getextrema()[3][0] != 0:
                raise RuntimeError(f"Generated pose '{name}' has no transparent background")
            image.verify()
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


def generate_missing() -> list[str]:
    made = []
    for name in POSE_NAMES:
        if not (ASSETS_DIR / "character" / "poses" / f"{name}.png").exists():
            generate_pose(name)
            made.append(name)
    return made
