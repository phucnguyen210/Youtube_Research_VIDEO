"""Regression checks for literal claim visuals and quality metadata."""
from core.hybrid_image_engine import prepare_image_plan


def main():
    lines = [
        ("Dopamine is not a toxin.", "not_a_toxin", {"poison_bottle", "reset_x", "brain"}),
        ("Twenty minutes disappear while you scroll.", "attention_capture", {"phone", "hourglass"}),
        ("Redesigning your surroundings changes the habit.", "environment_change", {"environment", "friction", "book"}),
    ]
    beats = [{"beat_id": str(i), "narration": line, "visual_archetype": "example",
              "character_visible": True, "focus_side": "center", "character_position": "left",
              "background_prompt": line} for i, (line, _, _) in enumerate(lines)]
    plan = prepare_image_plan([{"visual_beats": beats}], "balanced", False)
    for beat, (_, concept, required), entry in zip(beats, lines, plan):
        assert beat["visual_concept"] == concept, beat
        assert required.issubset({o["type"] for o in beat["visual_objects"]})
        assert 0 <= beat["visual_quality_score"] <= 1
        assert entry["visual_quality_score"] == beat["visual_quality_score"]
    assert beats[0]["scene_mode"] == "diagram"
    assert "reward" not in {o["type"] for o in beats[0]["visual_objects"]}
    print("VISUAL QUALITY TEST OK")


if __name__ == "__main__":
    main()
