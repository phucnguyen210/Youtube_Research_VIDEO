"""Acceptance checks for the dopamine detox visual mismatch regression."""
from pathlib import Path
from uuid import uuid4
from PIL import Image

from core.asset_composer import compose_assets
from core.hybrid_image_engine import HybridImageEngine, prepare_image_plan


NARRATIONS = [
    "There is no established biological milestone where, on day thirty, your dopamine receptors suddenly reset.",
    "So if there is no literal detox, what might actually change?",
    "The answer is your behavior, your environment, and your routines.",
    "Imagine this familiar sequence.",
    "Your phone buzzes.",
    "You see a notification.",
    "You open the app.",
    "Then twenty minutes disappear.",
    "The habit can run almost by itself.",
    "Move distracting apps off the home screen.",
    "These changes create friction.",
    "Meet a friend.",
    "You feel bored.",
    "Your hand reaches for the phone before you have consciously decided to use it.",
    "You may start a task without checking first.",
]


def main():
    beats=[{"beat_id":f"{i}a","narration":text,"visual_archetype":"example",
            "character_visible":i in {7,14},"character_pose":"thinking",
            "focus_side":"center","background_prompt":text,"character_position":"left"}
           for i,text in enumerate(NARRATIONS,1)]
    scenes=[{"visual_beats":beats}]
    plan=prepare_image_plan(scenes,"balanced",False)
    assert len(plan)==15
    types=lambda i: {o["type"] for o in beats[i-1]["visual_objects"]}
    assert {"timeline","brain","reset_x"} <= types(1)
    assert {"behavior","environment","habit_loop"} <= types(3)
    assert {"notification","phone","reward"} <= types(4)
    assert {"phone","notification"} <= types(5)
    assert {"phone","hourglass"} <= types(8)
    assert all("calendar" not in types(i) and "checklist" not in types(i) for i in range(1,16))
    assert all(0<=b["asset_match_confidence"]<=1 and
               (b["visual_novelty_score"]>=.45 or b["continuity_group"])
               for b in beats)
    assert beats[13]["image_strategy"]=="full_scene_ai"
    folder=Path(__file__).parent/"projects"/"hybrid_test"
    folder.mkdir(parents=True,exist_ok=True)
    target=folder/"semantic_sample.png"
    compose_assets(beats[0],target,assets_dir=folder/"missing")
    with Image.open(target) as image: assert image.size==(2048,1152)
    class FakeSceneService:
        def __init__(self): self.calls=0
        def generate_full_scene(self,prompt,output_path,*,quality,size):
            self.calls+=1
            Image.new("RGB",(1536,1024),(225,220,205)).save(output_path)
    fake=FakeSceneService()
    engine=HybridImageEngine("balanced",False,fake,cache_dir=folder/"semantic_cache",global_limit=1)
    first={**beats[13],"narration":beats[13]["narration"]+uuid4().hex,"image_strategy":"full_scene_ai",
           "image_strategy_reason":"test"}
    engine.render_background(first,folder/"full_scene_test.png",{})
    assert fake.calls==1 and first["image_strategy"]=="full_scene_ai"
    second={**first,"narration":first["narration"]+" different","image_strategy":"full_scene_ai"}
    engine.render_background(second,folder/"full_scene_fallback.png",{})
    assert fake.calls==1 and second["image_strategy"]=="character_composite" and second["scene_mode"]=="host"
    print("SEMANTIC VISUAL TEST OK",{kind:sum(b["image_strategy"]==kind for b in beats)
                                     for kind in {b["image_strategy"] for b in beats}})


if __name__=="__main__": main()
