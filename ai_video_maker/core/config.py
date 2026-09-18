from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROJECTS_DIR = ROOT / "projects"
CACHE_IMAGES_DIR = ROOT / "cache" / "images"
ASSETS_DIR = ROOT / "assets"
CHARACTER_PATH = ASSETS_DIR / "character" / "main.png"
STYLE_REFERENCE_PATH = ASSETS_DIR / "style" / "reference_room.png"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-5.6-luna").strip()
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "openai").strip().lower()
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1-mini").strip()
IMAGE_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "medium").strip().lower()
MAX_AI_IMAGES_PER_PROJECT = max(0,int(os.getenv("MAX_AI_IMAGES_PER_PROJECT", "6")))
IMAGE_COST_ESTIMATE = {
    "low": float(os.getenv("IMAGE_COST_LOW_USD", "0.006")),
    "medium": float(os.getenv("IMAGE_COST_MEDIUM_USD", "0.015")),
    "high": float(os.getenv("IMAGE_COST_HIGH_USD", "0.052")),
}
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "marin").strip()
DEMO_MODE = os.getenv("DEMO_MODE", "0").strip() == "1"
MAX_SCENES = int(os.getenv("MAX_SCENES", "60"))

VIDEO_W = 1920
VIDEO_H = 1080

VISUAL_STYLE = """
Minimal 2D educational explainer illustration. Clean thin hand-drawn dark outlines,
white or warm off-white background, soft pastel yellow and neutral accent colors,
simple geometric objects, sparse composition, no complex textures, no photorealism,
no tiny decorative clutter, no people, no human silhouettes, no logos, no watermark.
Use large, readable visual metaphors and simple object relationships that a viewer can
understand in under one second. Keep a consistent visual language across every scene.
Use a clean minimal composition. No decorative rings, floating labels, top-center text,
random callouts, UI pill badges, or filler marks. Emphasis must explain the idea.
""".strip()

STORY_RULES = """
A visual storyteller does not merely illustrate each sentence. It chooses what the viewer should
feel, notice, compare, or understand next. Every scene must have a story purpose, one focal idea,
and a visual change that is motivated by the narration. Avoid repeating the same composition,
character placement, camera move, or visual metaphor across adjacent scenes. Mix character-led
beats with object-only beats. Use visual cause/effect, comparisons, reveals, before/after,
progression, and concrete metaphors when they genuinely fit the facts. Never add unsupported facts.
""".strip()

SCRIPT_RULES = """
Write for a broad non-technical audience. The viewer clicked because they are curious,
not because they want a report. Prioritize retention and clarity while staying faithful
to the research. Use short spoken sentences, plain English, concrete examples and
cause/effect language. Avoid unexplained jargon. If a technical term is necessary,
translate it immediately into everyday language. Open with a strong curiosity hook,
reveal information progressively, and make each sentence earn the next one. Never
fabricate a fact, statistic, quote or source just to make the script more exciting.
""".strip()
