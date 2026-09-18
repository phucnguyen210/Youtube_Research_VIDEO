"""Choose scene form, lived action, and continuity from planned meaning."""
from __future__ import annotations
import re

EXPERIENCE_RULES = (
    (r"wake|waking|alarm.*bed|grab.*phone", "bedroom", "reaching from bed toward the phone", "sleepy", ("bed","phone","window","alarm_clock"), .96),
    (r"stretch.*morning|morning.*stretch", "bedroom", "stretching beside the bed", "refreshed", ("bed","window","sun","mat"), .94),
    (r"sitting at.*desk|studying at.*desk|study.*late|late.*studying|writing.*notebook|study actively|closing your notes|finish one assignment", "study room at night", "sitting at the desk and writing", "focused", ("desk","chair","lamp","book","notebook","papers","mug","night_window"), .93),
    (r"gym|workout.*time|time.*exercise", "small gym", "hesitating beside exercise equipment", "doubtful", ("gym_bench","dumbbell","mirror","water"), .96),
    (r"move.*phone.*away|leave.*phone.*outside", "study room", "placing the phone away from the desk", "determined", ("phone","desk","chair","book","lamp"), .85),
    (r"phone buzz|see a notification|check.*notification|check.*app|unlock.*screen|open.*app", "bedroom desk", "picking up the phone and checking its screen", "curious", ("phone","notification","desk","chair","lamp"), .83),
    (r"scroll|minutes later|minute.*disappear", "bedroom desk", "scrolling the phone while time passes", "surprised", ("phone","chair","desk","hourglass","lamp"), .92),
    (r"waiting for a bus|walking.*break|take a walk|meet a friend|move during the day|take breaks", "outdoor walkway", "walking or pausing outdoors", "thoughtful", ("walking","conversation","sun","phone"), .82),
    (r"bored|urge|temptation|withdrawal|strangely empty|overwhelm", "quiet room", "pausing with the phone nearby but not touching it", "uneasy", ("phone","chair","window","book"), .79),
    (r"pack.*night|prepare.*tomorrow|planning tomorrow|getting ready.*night", "bedroom at night", "packing study materials beside the desk", "focused", ("desk","book","notebook","bag","lamp","night_window"), .9),
)
DIAGRAM_CONCEPTS={"not_a_toxin","no_magic_reset","myth_vs_reality","habit_loop","brain_misconception",
                  "reward_loop","behavior_change","cause_effect","comparison","timeline","progress",
                  "priority","friction","active_recall"}
DIAGRAM_ARCHETYPES={"comparison","process","cause_effect","timeline","checklist","supply_flow","object_only"}

FULL_SCENE_CONCEPTS = {
    "not_a_toxin": ("quiet study room", "looking at a crossed-out poison-bottle sketch beside a simple brain sketch", "reassured"),
    "no_magic_reset": ("quiet study room", "looking at a crossed-out reset symbol on a calendar page", "skeptical"),
    "myth_vs_reality": ("quiet study room", "moving a false reset sketch aside and returning to an ordinary routine", "clear-minded"),
    "habit_loop": ("bedroom desk", "noticing the phone as a habit cue and pausing before touching it", "tempted"),
    "reward_loop": ("quiet study room", "looking at a simple brain-signal drawing in an open notebook", "curious"),
    "behavior_change": ("study room", "putting the phone aside and opening a book", "determined"),
    "active_recall": ("study room", "closing notes and recalling an answer from memory", "focused"),
    "priority": ("study room", "choosing one notebook task to begin", "focused"),
    "friction": ("study room", "placing the phone beyond arm's reach", "determined"),
}


def direct_beat(beat: dict) -> None:
    text=" ".join(str(beat.get("narration", "")).lower().split())
    concept=beat.get("visual_concept", "conceptual")
    suggested=None
    for pattern,environment,action,emotion,props,value in EXPERIENCE_RULES:
        if re.search(pattern,text):
            suggested=(environment,action,emotion,props,value)
            break
    if suggested is None and concept=="lived_experience":
        suggested=("bedroom desk","reaching for and using the phone","tempted",
                   ("phone","desk","chair","lamp","window"),.92)
    if suggested and re.search(r"phone buzz",text):
        suggested=(suggested[0],"turning toward a vibrating phone on the desk","alert",suggested[3],suggested[4])
    elif suggested and re.search(r"see a notification|check.*notification",text):
        suggested=(suggested[0],"looking closely at the phone notification","curious",suggested[3],suggested[4])
    elif suggested and re.search(r"unlock.*screen|open.*app|check.*app",text):
        suggested=(suggested[0],"tapping the phone to open the app","tempted",suggested[3],suggested[4])
    elif suggested and re.search(r"minutes later|minute.*disappear",text):
        suggested=(suggested[0],"looking up from the phone after time has passed","surprised",suggested[3],suggested[4])
    diagram=(concept in DIAGRAM_CONCEPTS or beat.get("visual_archetype") in DIAGRAM_ARCHETYPES)
    if suggested and concept not in {"not_a_toxin","no_magic_reset","brain_misconception","myth_vs_reality"}:
        environment,action,emotion,props,value=suggested
        beat.update(scene_mode="experiential",environment=environment,
                    character_action_description=action,emotion_description=emotion,
                    supporting_objects=list(props),story_value=value)
        beat["character_visible"]=True
    elif concept=="complex_environment":
        beat.update(scene_mode="experiential",environment="custom story environment",
                    character_action_description="reacting to the imagined situation",
                    emotion_description="expressive",supporting_objects=[o["type"] for o in beat.get("visual_objects",[])],
                    story_value=.7)
        beat["character_visible"]=True
    elif diagram and beat.get("asset_match_confidence",0)>=.55:
        beat.update(scene_mode="diagram",environment="clean explainer canvas",
                    character_action_description="not needed",emotion_description="neutral",
                    supporting_objects=[o["type"] for o in beat.get("visual_objects",[])],story_value=.15)
        beat["character_visible"]=False
    elif beat.get("character_visible") or concept=="conceptual":
        beat.update(scene_mode="host",environment="simple presentation space",
                    character_action_description="presenting the visual idea with one clear gesture",
                    emotion_description=str(beat.get("character_emotion","thoughtful")),
                    supporting_objects=[o["type"] for o in beat.get("visual_objects",[])],story_value=.25)
        beat["character_visible"]=True
    else:
        beat.update(scene_mode="diagram",environment="clean explainer canvas",
                    character_action_description="not needed",emotion_description="neutral",
                    supporting_objects=[o["type"] for o in beat.get("visual_objects",[])],story_value=.15)
        beat["character_visible"]=False
    beat["body_posture_description"]=("seated and leaning toward the work" if "sitting" in beat["character_action_description"]
                                     else "natural posture driven by the action")
    beat["object_interaction_description"]=(beat["character_action_description"] if beat["scene_mode"]=="experiential"
                                            else "gestures toward the focal object")
    beat["composition_template"]=("integrated_room" if beat["scene_mode"]=="experiential"
                                  else "presenter" if beat["scene_mode"]=="host"
                                  else beat.get("visual_layout","horizontal"))
    quote=re.search(r"(?:tell yourself|promise yourself|think)\s+[\"“']([^\"”']{8,55})[\"”']",str(beat.get("narration","")),re.I)
    beat["speech_bubble_text"]=quote.group(1).strip() if quote else ""
    if not beat["speech_bubble_text"] and beat["scene_mode"]=="experiential":
        if "gym" in beat["environment"] and re.search(r"i don.t have time to exercise",text):
            beat["speech_bubble_text"]="I don't have time to exercise in the morning."
        elif re.search(r"just one notification|only check one notification",text):
            beat["speech_bubble_text"]="Just one notification."


def assign_continuity(beats: list[dict]) -> None:
    """Keep adjacent phone or routine actions in the same illustrated location."""
    counter=0; active_kind=None; active_id=None
    for beat in beats:
        text=str(beat.get("narration", "")).lower()
        concept=beat.get("visual_concept")
        if concept in {"habit_loop","notification_trigger","phone_scrolling","attention_capture","automatic_behavior"} and (
                "phone" in text or "notification" in text or concept in {"phone_scrolling","attention_capture"}):
            kind="phone_loop"
        elif active_kind=="phone_loop" and concept=="lived_experience" and re.search(r"minutes later|minute.*disappear|phone",text):
            kind="phone_loop"
        elif concept in {"brain_misconception","myth_vs_reality"}:
            kind="reset_myth"
        elif concept in {"habit_loop","automatic_behavior"}:
            kind="habit_explain"
        elif concept=="friction" and re.search(r"app|phone|internet|friction",text):
            kind="phone_setup"
        elif concept=="sleep" and re.search(r"sleep|hour|teenager|adult|seven|eight|ten",text):
            kind="sleep_explain"
        elif beat.get("scene_mode")=="experiential" and beat.get("environment","" ).startswith("bedroom") and re.search(r"wake|morning|stretch|bed",text):
            kind="morning_room"
        elif beat.get("scene_mode")=="experiential" and ("study" in text or "desk" in text or "pack" in text):
            kind="study_room"
        else:
            kind=None
        if kind is None:
            active_kind=None; active_id=None
            beat["continuity_group"]=""
            continue
        if kind!=active_kind:
            counter+=1; active_id=f"{kind}_{counter:02d}"
            active_kind=kind
        beat["continuity_group"]=active_id
        if kind=="phone_loop":
            beat["environment"]="bedroom desk"
            beat["supporting_objects"]=list(dict.fromkeys(["phone","desk","chair","lamp","window",*beat["supporting_objects"]]))[:8]
            beat["composition_template"]="same bedroom desk, same window and lamp; vary camera only"
        elif kind=="morning_room": beat["environment"]="bedroom morning"
        elif kind=="study_room": beat["environment"]="study room at night"


def allocate_experiential_budget(beats: list[dict], cap: int) -> None:
    """Reserve limited full-scene calls for strongest moments before rendering."""
    candidates=[(i,b) for i,b in enumerate(beats) if b.get("scene_mode")=="experiential"]
    ranked=sorted(candidates,key=lambda pair:pair[1].get("story_value",0),reverse=True)
    keep=set(); groups=set()
    if cap>0:
        for i,beat in ranked:
            group=beat.get("continuity_group") or f"standalone_{i}"
            if group in groups: continue
            keep.add(i); groups.add(group)
            if len(keep)>=cap: break
        for i,_ in ranked:
            if len(keep)>=cap: break
            keep.add(i)
    for i,beat in candidates:
        if i not in keep:
            beat["scene_mode"]="host"
            beat["composition_template"]="presenter_in_context"
            semantic=[o["type"] for o in beat.get("visual_objects",[])
                      if o.get("type") not in {"idea","action"}]
            props=list(dict.fromkeys([*semantic,*beat.get("supporting_objects",[])]))[:4]
            if props:
                beat["visual_objects"]=[{"type":name,"importance":"primary" if j==0 else "secondary",
                                         "position_hint":("left","center","right")[j%3],"count":1}
                                        for j,name in enumerate(props)]
            beat["budget_downgrade_reason"]="full-scene budget reserved for stronger story moments"
