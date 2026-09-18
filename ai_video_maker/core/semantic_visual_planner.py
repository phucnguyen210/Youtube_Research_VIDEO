"""Plan the visual claim before choosing assets; unknown claims stay unknown."""
from __future__ import annotations
import re

def _objects(*names):
    return [{"type": name, "importance": "primary" if i == 0 else "secondary",
             "position_hint": ("left", "center", "right")[i % 3], "count": 1}
            for i, name in enumerate(names)]

def plan_semantic_visual(beat: dict) -> dict:
    text = " ".join(str(beat.get("narration", "")).lower().split())
    purpose = " ".join(str(beat.get("story_purpose", "")).lower().split())
    concept, subject, message, objects, relation, confidence = (
        "conceptual", "spoken idea", "Show the spoken idea as one clear relationship",
        ("idea", "action"), "related", .38)
    def match(pattern): return bool(re.search(pattern, text))
    if match(r"dopamine (?:is|isn't|is not|was|wasn't|was not).{0,20}(?:not|n't|never).{0,12}(?:a )?(?:toxin|poison)") or match(r"dopamine (?:isn't|is not|wasn't|was not) (?:a )?(?:toxin|poison)"):
        concept,subject,message,objects,relation,confidence = "not_a_toxin","dopamine is not a toxin","Reject the false idea that dopamine is a poison; show dopamine as a normal brain signal",("poison_bottle","reset_x","brain"),"negates",.98
    elif match(r"surreal|dreamlike|abstract metaphor|imaginary world|information overload"):
        concept,subject,message,objects,relation,confidence = "complex_environment","abstract concept","Illustrate the abstract idea as one coherent custom environment",("idea","attention"),"metaphor",.3
    elif match(r"factory settings|restore it|scientific.*detox"):
        concept,subject,message,objects,relation,confidence = "brain_misconception","brain reset myth","Show the false factory-reset idea crossed out",("brain","reset_x"),"negates",.89
    elif match(r"no established biological milestone|receptors.*reset|day thirty.*reset|30 days.*reset"):
        concept,subject,message,objects,relation,confidence = "no_magic_reset","dopamine reset misconception","Day 30 is not a biological reset point",("timeline","brain","reset_x"),"negates",.94
    elif match(r"no literal detox|not a literal detox|what might actually change"):
        concept,subject,message,objects,relation,confidence = "myth_vs_reality","what changes instead of a detox","Replace the brain-reset myth with behavior, environment and routine",("reset_x","behavior","environment","habit_loop"),"replacement",.91
    elif all(w in text for w in ("behavior","environment","routine")):
        concept,subject,message,objects,relation,confidence = "behavior_change","behavior, environment and routines","Show three real levers: behavior, environment and routine",("behavior","environment","habit_loop"),"three_part",.96
    elif match(r"familiar sequence|cue.driven habit|automatic behavior|habit loop|triggered by a signal"):
        concept,subject,message,objects,relation,confidence = "habit_loop","cue-action-reward habit","Show cue to action to reward",("notification","phone","reward"),"sequence",.93
    elif match(r"phone buzz|phone vibrat"):
        concept,subject,message,objects,relation,confidence = "notification_trigger","phone buzz","Show a phone vibrating on a desk",("phone","notification","desk"),"trigger",.98
    elif match(r"no notification"):
        concept,subject,message,objects,relation,confidence = "boredom","internal habit cue","Show the phone habit starting without any alert",("phone","notification_off","urge"),"absence",.88
    elif "notification" in text:
        concept,subject,message,objects,relation,confidence = "notification_trigger","phone notification","Show a notification appearing on a phone",("phone","notification"),"overlay",.97
    elif match(r"minute.*disappear|minutes later|time pass|lose track of time"):
        concept,subject,message,objects,relation,confidence = "attention_capture","time lost to the phone","Show time passing while attention stays on the phone",("phone","hourglass","attention"),"time_passage",.9
    elif match(r"hand reaches for the phone|before you.*decid|without thinking"):
        concept,subject,message,objects,relation,confidence = "automatic_behavior","automatic phone reach","Show a cue leading automatically to phone use",("notification","behavior","phone"),"sequence",.88
    elif match(r"move distracting apps|home screen|block mobile internet|outside the bedroom"):
        concept,subject,message,objects,relation,confidence = "friction","changing phone access","Show a barrier between cue and phone use",("phone","friction","environment"),"barrier",.91
    elif match(r"unlock.*screen|open.*app|check.*app|scroll|social media|watching something"):
        concept,subject,message,objects,relation,confidence = "phone_scrolling","phone use","Show the phone action and what it leads to",("phone","social_media"),"action",.9
    elif match(r"dopamine.*not.*tank|dopamine.*not.*empt|flush dopamine|run out of it"):
        concept,subject,message,objects,relation,confidence = "brain_misconception","dopamine misconception","Cross out the false idea of dopamine as an empty tank",("brain","tank","reset_x"),"negates",.89
    elif match(r"motivation, learning|signals related to rewards"):
        concept,subject,message,objects,relation,confidence = "reward_loop","dopamine functions","Show brain signals supporting motivation and learning",("brain","reward","book"),"signal",.86
    elif match(r"dopamine|neurotransmitter|receptor|brain|reward system"):
        concept,subject,message,objects,relation,confidence = "reward_loop","brain reward signals","Show brain reward-related signals",("brain","reward"),"signal",.82
    elif match(r"bored|boredom|waiting for a bus"):
        concept,subject,message,objects,relation,confidence = "boredom","boredom cue","Show a quiet pause that can trigger phone use",("person","phone","hourglass"),"temptation",.82
    elif match(r"tired.*stud|stud.*late at night|late.night study"):
        concept,subject,message,objects,relation,confidence = "study_stress","late-night studying","Show a tired student working at a desk late at night",("desk","lamp","book","night_window"),"lived_moment",.91
    elif match(r"plan tomorrow|planning tomorrow"):
        concept,subject,message,objects,relation,confidence = "priority","preparing tomorrow","Show study materials prepared for tomorrow's first action",("priority_cards","bag","notebook"),"sequence",.88
    elif match(r"too little sleep|sleep.*hurt.*attention|sleep.*hurt.*memory"):
        concept,subject,message,objects,relation,confidence = "cause_effect","sleep and cognition","Show lost sleep reducing attention for study",("bed","focus","book"),"cause_effect",.87
    elif match(r"sleep|bedtime|night") or ("sleep" in purpose and match(r"teenager|adult|hours|seven|eight|ten")):
        concept,subject,message,objects,relation,confidence = "sleep","sleep","Show sleep as a concrete behavior",("bed","moon"),"group",.91
    elif match(r"important task|easiest thing to begin|priorit|assignment|vocabulary"):
        concept,subject,message,objects,relation,confidence = "priority","small daily priorities","Show a few specific study priorities",("priority_cards","book","notebook"),"group",.87
    elif match(r"material before checking|checking the answer|active recall|closing your notes") or "active-recall" in purpose:
        concept,subject,message,objects,relation,confidence = "active_recall","retrieving knowledge","Show notes closed, recall first, answer checked after",("notebook","brain","book"),"sequence",.87
    elif match(r"exercise|workout|walk"):
        concept,subject,message,objects,relation,confidence = "exercise","physical activity","Show movement replacing screen time",("walking","exercise"),"replacement",.88
    elif match(r"read|book"):
        concept,subject,message,objects,relation,confidence = "replacement_behavior","reading","Show reading as an alternative action",("book","phone"),"replacement",.85
    elif match(r"focus|concentrat|attention"):
        concept,subject,message,objects,relation,confidence = "focus","attention","Show attention directed to one task",("focus","book"),"focus",.81
    elif match(r"move.*phone.*away|phone.*away|leave.*phone.*outside"):
        concept,subject,message,objects,relation,confidence = "friction","phone out of reach","Show the phone moved away from the study area",("phone","desk","friction"),"barrier",.91
    elif match(r"calendar|schedule|plan for tomorrow|day-by-day timeline"):
        concept,subject,message,objects,relation,confidence = "timeline","schedule","Show the sequence of planned days",("calendar","timeline"),"sequence",.85
    elif match(r"checklist|to-do list|list of tasks"):
        concept,subject,message,objects,relation,confidence = "progress","tasks","Show task progress",("checklist","progress"),"group",.85
    elif match(r"ram|memory chip|dram"):
        concept,subject,message,objects,relation,confidence = "cause_effect","computer memory","Show RAM and its relation to demand",("ram","server"),"cause_effect",.86
    elif match(r"factory|supply chain|production capacity"):
        concept,subject,message,objects,relation,confidence = "cause_effect","supply","Show supply moving from factory to buyer",("factory","ram","price"),"sequence",.83
    elif match(r"alarm|wake up|morning routine"):
        concept,subject,message,objects,relation,confidence = "routine_change","waking routine","Show the wake-up action",("alarm_clock","bed"),"group",.88
    elif match(r"price|expensive|cost"):
        concept,subject,message,objects,relation,confidence = "comparison","price change","Show a price comparison",("price","ram"),"comparison",.82
    elif match(r"cue and.*behavior.*linked|habit can run|careful decision|automatic reflex|less automatic"):
        concept,subject,message,objects,relation,confidence = "automatic_behavior","learned automatic habit","Show a cue turning into an automatic phone action",("notification","habit_loop","phone"),"sequence",.84
    elif match(r"changing the situation|redesigning your surroundings|stimulus control|unwanted behavior|better alternatives|what replaces|screen time"):
        concept,subject,message,objects,relation,confidence = "environment_change","changing habit conditions","Show the environment steering a replacement behavior",("environment","friction","book"),"replacement",.85
    elif match(r"friction|harder to start|pause before acting"):
        concept,subject,message,objects,relation,confidence = "friction","barrier to habit","Show a barrier interrupting the phone habit",("phone","friction","habit_loop"),"barrier",.9
    elif match(r"friend|conversation|outdoors|being outdoors"):
        concept,subject,message,objects,relation,confidence = "replacement_behavior","social or outdoor alternative","Show a real-world activity replacing screen time",("conversation","walking"),"replacement",.85
    elif match(r"first part.*feel|first days|strangely empty|withdrawal|uncomfortable|discomfort|urge"):
        concept,subject,message,objects,relation,confidence = "urge","discomfort after habit change","Show the urge without portraying a chemical detox",("person","urge","phone"),"temptation",.83
    elif match(r"waiting|quiet moment|day feel slower|between tasks|during meals"):
        concept,subject,message,objects,relation,confidence = "boredom","quiet moments","Show time and attention during an ordinary pause",("person","hourglass","phone"),"time_passage",.81
    elif match(r"routine|habit|linked|connected"):
        concept,subject,message,objects,relation,confidence = "habit_loop","repeated habit","Show a repeated cue-action-reward pattern",("notification","phone","reward"),"sequence",.76
    elif match(r"not evidence|not what happens|no chemical detox"):
        concept,subject,message,objects,relation,confidence = "myth_vs_reality","false detox explanation","Cross out the biological reset myth",("brain","reset_x"),"negates",.82
    elif match(r"start a task|task without checking"):
        concept,subject,message,objects,relation,confidence = "focus","starting a task","Show attention moving from phone to task",("phone","focus","book"),"replacement",.83
    elif match(r"progress|notice|discover|information|reflect"):
        concept,subject,message,objects,relation,confidence = "reflection","recognizing behavior","Show observation of a habit pattern",("attention","habit_loop"),"reflection",.75
    if confidence < .55 and beat.get("text_visual_message"):
        from .asset_composer import GROUPS
        candidates=[str(item.get("type","")).lower().replace(" ","_")
                    for item in beat.get("text_visual_objects",[]) if isinstance(item,dict)]
        supported=[name for name in candidates if name in GROUPS]
        if supported:
            subject=str(beat.get("text_semantic_subject") or subject)[:120]
            message=str(beat["text_visual_message"])[:240]
            concept=str(beat.get("text_visual_concept") or "conceptual")[:80]
            relation=str(beat.get("text_visual_relationship") or "group")[:40]
            objects=tuple(supported[:5]); confidence=.72
    if beat.get("character_visible") and match(r"minutes later.*watching|feel strangely empty|feel like withdrawal|phone before.*decided"):
        concept="lived_experience"
        message="Show the character experiencing this specific moment: " + text.rstrip(".?!")
        confidence=.42
    return {"semantic_planner_version":3,"semantic_subject":subject,"core_claim":text.rstrip(".?!"),"visual_message":message,
            "visual_metaphor":concept,"visual_action":relation,"visual_relationship":relation,
            "visual_concept":concept,"visual_objects":_objects(*objects),
            "asset_match_confidence":confidence}
