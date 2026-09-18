"""Score and vary adjacent compositions without changing the claim."""
from __future__ import annotations

LAYOUTS = ("horizontal", "vertical", "triangle", "focus")
ALTERNATIVES = {
    "brain_misconception": ("brain","reset_x"),
    "habit_loop": ("habit_loop","phone","reward"),
    "automatic_behavior": ("behavior","habit_loop","phone"),
    "reward_loop": ("brain","attention","reward"),
    "exercise": ("walking","environment","exercise"),
    "urge": ("person","urge","habit_loop"),
    "boredom": ("person","attention","hourglass"),
    "friction": ("phone","notification_off","friction"),
    "environment_change": ("environment","habit_loop","book"),
}

def visual_signature(beat: dict) -> dict:
    return {"assets": frozenset(o["type"] for o in beat.get("visual_objects",[])),
            "layout": beat.get("visual_layout", "horizontal"),
            "archetype": beat.get("visual_archetype"),
            "character": beat.get("character_pose") if beat.get("character_visible") else None,
            "focus_side": beat.get("focus_side"),
            "scene_mode":beat.get("scene_mode"),"visual_concept":beat.get("visual_concept"),
            "environment":beat.get("environment"),"composition":beat.get("composition_template"),
            "character_action":beat.get("character_action_description"),
            "emotion":beat.get("emotion_description"),
            "continuity_group":beat.get("continuity_group", "")}

def novelty_score(current: dict, previous: list[dict]) -> float:
    if not previous: return 1.0
    weights={"assets":.28,"layout":.12,"archetype":.06,"character":.04,"focus_side":.06,
             "scene_mode":.09,"visual_concept":.13,"environment":.05,
             "composition":.05,"character_action":.09,"emotion":.03}
    return round(min(sum(weight for field,weight in weights.items()
                         if current[field]!=old[field]) for old in previous[-3:]),2)

def guard_visual_repetition(beats: list[dict]) -> list[str]:
    warnings=[]; history=[]
    for beat in beats:
        beat.setdefault("visual_layout", "horizontal")
        signature=visual_signature(beat)
        score=novelty_score(signature,history)
        repeated_assets=(len(history)>=2 and signature["assets"]==history[-1]["assets"]==history[-2]["assets"])
        continuity=bool(beat.get("continuity_group") and len(history)>0 and
                        beat["continuity_group"]==history[-1].get("continuity_group"))
        if (score < .45 or repeated_assets) and beat.get("visual_concept") != "timeline" and not (continuity and score>=.32 and not repeated_assets):
            alternate=ALTERNATIVES.get(beat.get("visual_concept"))
            if alternate and frozenset(alternate)!=signature["assets"]:
                original=beat["visual_objects"]
                beat["visual_objects"]=[{"type":name,"importance":"primary" if i==0 else "secondary",
                                         "position_hint":("left","center","right")[i%3],"count":1}
                                        for i,name in enumerate(alternate)]
                candidate=visual_signature(beat)
                improved=novelty_score(candidate,history)
                if improved>score or repeated_assets: signature,score=candidate,improved
                else: beat["visual_objects"]=original
            for layout in LAYOUTS:
                if layout==beat["visual_layout"]: continue
                beat["visual_layout"]=layout
                if beat.get("scene_mode")=="diagram": beat["composition_template"]=layout
                candidate=visual_signature(beat)
                improved=novelty_score(candidate,history)
                if improved>score: signature,score=candidate,improved
                if score>=.45: break
            if score<.45 and beat.get("scene_mode")=="diagram":
                beat["focus_side"]="right" if beat.get("focus_side")!="right" else "left"
                candidate=visual_signature(beat)
                improved=novelty_score(candidate,history)
                if improved>score: signature,score=candidate,improved
            if score<.45:
                beat["visual_repetition_warning"]="similar to recent beats; semantic plan preserved"
                warnings.append(f"{beat['beat_id']}: repeated visual composition")
        beat["visual_novelty_score"]=score
        history.append(signature)
    return warnings
