"""The optional illustrated-video switch covers every beat without bypassing Demo safety."""
import json
from pathlib import Path

from core.hybrid_image_engine import HybridImageEngine, prepare_image_plan
from core.integrated_scene import build_integrated_scene_prompt


def main():
    for project_id in ("a84b76037025", "dff77a022805"):
        scenes = json.loads((Path("projects") / project_id / "scenes.json").read_text(encoding="utf-8"))
        plan = prepare_image_plan(scenes, "balanced", False, True)
        assert plan and all(item["strategy"] == "full_scene_ai" for item in plan)
        assert all(b["scene_mode"] == "experiential" for s in scenes for b in s["visual_beats"])
        assert max(len(b["supporting_objects"]) for s in scenes for b in s["visual_beats"]) <= 3
        engine = HybridImageEngine("balanced", False, None, full_scene_mode=True, planned_beats=len(plan))
        assert engine.limit == len(plan)
        print(project_id, len(plan), "full scenes planned")
    prompt = build_integrated_scene_prompt(scenes[0]["visual_beats"][0])
    assert "at most two quiet background objects" in prompt
    three_minutes = [{"visual_beats": [{"beat_id": f"{i}",
                   "narration": "A student sits at a desk studying, then puts the phone away.",
                   "visual_archetype": "example", "character_visible": True}]}
                     for i in range(45)]
    three_minute_plan = prepare_image_plan(three_minutes, "balanced", False, True)
    assert len(three_minute_plan) == 45
    assert all(item["strategy"] == "full_scene_ai" for item in three_minute_plan)
    print("synthetic 3-minute storyboard", len(three_minute_plan), "full scenes planned")
    demo = [{"visual_beats": [{"beat_id": "1", "narration": "A student wakes up in bed.",
                                "visual_archetype": "example", "character_visible": True}]}]
    assert prepare_image_plan(demo, "balanced", True, True)[0]["strategy"] != "full_scene_ai"
    print("FULL SCENE MODE TEST OK")


if __name__ == "__main__":
    main()
