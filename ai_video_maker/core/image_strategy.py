"""Cost modes and strategy selection from a semantic visual plan."""
from __future__ import annotations

MODE_LIMITS = {"low_cost": 2, "balanced": 6, "high_quality": 8}
MODE_QUALITY = {"low_cost": "low", "balanced": "medium", "high_quality": "high"}


def plan_visual_objects(beat: dict) -> list[dict]:
    """Compatibility entry point; semantic planning owns object selection."""
    if beat.get("semantic_planner_version") != 3:
        from .semantic_visual_planner import plan_semantic_visual
        beat.update(plan_semantic_visual(beat))
    return beat["visual_objects"]


def select_image_strategy(beat: dict, mode: str = "balanced", demo_mode: bool = False) -> tuple[str, str]:
    if "visual_message" not in beat:
        plan_visual_objects(beat)
    if "scene_mode" not in beat:
        from .scene_director import direct_beat
        direct_beat(beat)
    mode_name=beat["scene_mode"]
    if demo_mode and mode_name=="experiential":
        beat["scene_mode"]="host"; mode_name="host"
    mapping={"diagram":"asset_composer","host":"character_composite","experiential":"full_scene_ai"}
    return mapping[mode_name], {"diagram":"semantic diagram", "host":"character presents a contextual visual",
                                "experiential":"integrated lived action and environment"}[mode_name]


def mode_limit(mode: str, global_limit: int) -> int:
    return max(0, min(MODE_LIMITS.get(mode, 6), global_limit))
