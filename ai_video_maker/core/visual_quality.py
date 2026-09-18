"""Cheap, deterministic checks before paying for an image or drawing a local scene."""
from __future__ import annotations

SENSITIVE = {
    "not_a_toxin": ({"poison_bottle", "reset_x", "brain"}, {"reward", "calendar", "checklist"}),
    "no_magic_reset": ({"reset_x", "brain"}, {"calendar", "checklist"}),
    "attention_capture": ({"phone", "hourglass"}, {"calendar", "checklist"}),
    "environment_change": ({"environment", "friction", "book"}, {"calendar", "checklist"}),
}
GENERIC = {"idea", "action", "person"}


def audit_visual(beat: dict) -> None:
    """Repair known wrong visual metaphors and record a bounded quality estimate."""
    concept = beat.get("visual_concept", "")
    names = [str(o.get("type", "")) for o in beat.get("visual_objects", [])]
    mismatch = ""
    if concept in SENSITIVE:
        required, forbidden = SENSITIVE[concept]
        if not required.issubset(names) or forbidden.intersection(names):
            mismatch = "claim-specific visual objects replaced"
            names = list(required)
            beat["visual_objects"] = [
                {"type": name, "importance": "primary" if i == 0 else "secondary",
                 "position_hint": ("left", "center", "right")[i % 3], "count": 1}
                for i, name in enumerate(names)
            ]
    if concept == "not_a_toxin" and not beat.get("full_scene_mode"):
        beat["scene_mode"] = "diagram"
        beat["character_visible"] = False
    concrete = [name for name in names if name not in GENERIC]
    confidence = float(beat.get("asset_match_confidence", 0))
    relationship = beat.get("visual_relationship", "related")
    score = (.27 * confidence + .22 * min(len(concrete), 3) / 3
             + .16 * bool(relationship not in {"related", "group"})
             + .14 * bool(beat.get("visual_message"))
             + .11 * bool(beat.get("scene_mode") == "experiential" or len(concrete) >= 2)
             + .10 * float(beat.get("visual_novelty_score", .7)))
    if not concrete:
        score = min(score, .39)
    beat["visual_quality_score"] = round(min(1.0, max(0.0, score)), 2)
    beat["semantic_mismatch"] = mismatch
    beat["visual_quality_warning"] = "weak visual plan; review before paid render" if score < .55 else ""
