"""Acceptance checks for three modes, continuity, and integrated prompts."""
from collections import Counter
from core.hybrid_image_engine import prepare_image_plan
from core.integrated_scene import build_integrated_scene_prompt
from core.image_strategy import plan_visual_objects
from core.scene_director import direct_beat

DAILY=[
    "You wake up and reach for your phone from bed.",
    "Instead, stretch beside your bed in the morning light.",
    "Sit at your desk and write in your notebook.",
    "Choose three priorities for today's study session.",
    "Study actively by closing your notes and recalling the answer.",
    "Walk during a short break.",
    "Your phone buzzes on the desk.",
    "You see a notification.",
    "You open the app.",
    "Then twenty minutes disappear.",
    "Move distracting apps off the home screen.",
    "Take a break and drink water.",
    "Pack your study materials at night.",
    "Plan tomorrow's first task before bed.",
    "A tired student sits at a desk studying late at night under a lamp.",
]


def main():
    beats=[{"beat_id":f"{i}a","narration":text,"visual_archetype":"example",
            "character_visible":True,"character_pose":"working","focus_side":"center",
            "character_position":"left","background_prompt":text}
           for i,text in enumerate(DAILY,1)]
    prepare_image_plan([{"visual_beats":beats}],"balanced",False)
    counts=Counter(b["scene_mode"] for b in beats)
    assert set(counts)=={"diagram","host","experiential"}
    assert counts["experiential"]==4
    assert all({"diagram":"asset_composer","host":"character_composite",
                "experiential":"full_scene_ai"}[b["scene_mode"]]==b["image_strategy"] for b in beats)
    assert len({b["continuity_group"] for b in beats[6:10]})==1
    assert len({b["environment"] for b in beats[6:10]})==1
    assert len({b["character_action_description"] for b in beats[6:10]})>=3
    assert all(b["visual_novelty_score"]>=.45 or b["continuity_group"] for b in beats)
    late=beats[14]
    prompt=build_integrated_scene_prompt(late)
    for fragment in ("short black hair","pale mint-green shirt","sitting at the desk",
                     "study room at night","lamp","night_window","No speech bubble"):
        assert fragment in prompt
    gym={**late,"visual_message":"Show hesitation before a workout",
         "environment":"small gym","character_action_description":"hesitating beside gym equipment",
         "emotion_description":"doubtful","supporting_objects":["gym_bench","dumbbell","mirror"],
         "speech_bubble_text":"I don't have time to exercise in the morning."}
    gym_prompt=build_integrated_scene_prompt(gym)
    assert "small gym" in gym_prompt and "I don't have time to exercise in the morning." in gym_prompt
    selected_gym={"narration":"I don't have time to exercise in the morning at the gym.",
                  "visual_archetype":"example","character_visible":True}
    plan_visual_objects(selected_gym); direct_beat(selected_gym)
    assert selected_gym["scene_mode"]=="experiential"
    assert selected_gym["environment"]=="small gym"
    assert selected_gym["speech_bubble_text"]=="I don't have time to exercise in the morning."
    print("SCENE DIRECTOR TEST OK",dict(counts))


if __name__=="__main__": main()
