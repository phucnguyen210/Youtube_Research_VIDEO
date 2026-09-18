"""Deterministic visual beat planning, including legacy scene conversion."""
from __future__ import annotations

import re
from .character_pose_selector import requested_pose
from .overlays import normalize_overlays

TRANSITIONS = re.compile(r"\b(?:but|however|meanwhile|instead|while|because|so|therefore|as a result|this means)\b", re.I)
SENTENCES = re.compile(r"(?<=[.!?])\s+")


def split_narration(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    parts = SENTENCES.split(text)
    clauses = []
    for part in parts:
        clauses.extend(re.split(r"(?<=[,;:])\s+(?=(?:but|however|meanwhile|instead|while|because|so|therefore|as a result|this means)\b)", part, flags=re.I))
    result = []
    for clause in clauses:
        words = clause.split()
        while len(words) > 16:
            cut = min(14, len(words) - 6)
            result.append(" ".join(words[:cut]))
            words = words[cut:]
        if words:
            result.append(" ".join(words))
    return result


def _archetype(text: str, fallback: str) -> str:
    low = text.lower()
    if re.search(r"\b(that leaves|leaves fewer|less supply|fewer chips|consequence)\b", low):
        return "consequence"
    if re.search(r"\b(because|so|therefore|as a result|this means|leaves|leads to)\b", low):
        return "cause_effect"
    if re.search(r"\b(but|however|instead|while|versus|compared)\b", low):
        return "comparison"
    if "?" in text:
        return "question_reveal"
    return fallback


def plan_visual_beats(scene: dict) -> list[dict]:
    existing = scene.get("visual_beats")
    if isinstance(existing, list) and existing:
        chunks = []
        for raw in existing:
            narration = raw.get("narration", "")
            parts = split_narration(narration) if len(narration.split()) > 16 else [narration]
            chunks.extend({**raw, "narration": part, "beat_id": raw.get("beat_id") if len(parts)==1 else None} for part in parts)
    else:
        narration = scene.get("narration", "")
        words = len(narration.split())
        estimated = words / 145 * 60
        needs_split = words > 22 or estimated > 7 or bool(TRANSITIONS.search(narration)) or len(SENTENCES.split(narration.strip())) > 2
        chunks = [{"narration": part} for part in (split_narration(narration) if needs_split else [narration])]
    beats = []
    for index, raw in enumerate(chunks):
        beat = dict(raw)
        narration = beat.get("narration") or scene.get("narration", "")
        arch = beat.get("visual_archetype") or _archetype(narration, scene.get("visual_archetype", "example"))
        beat.update({
            "beat_id": beat.get("beat_id") or f"{scene['scene_id']}{chr(97 + index) if index < 26 else f'_{index+1}'}",
            "scene_id": scene["scene_id"],
            "narration": narration,
            "story_purpose": beat.get("story_purpose") or scene.get("story_purpose", "explain one idea"),
            "viewer_feeling": beat.get("viewer_feeling") or scene.get("viewer_feeling", "clear"),
            "visual_archetype": arch,
            "focus_object": beat.get("focus_object") or narration.strip(" .")[:100] or scene.get("focus_object", "main idea"),
            "focus_side": beat.get("focus_side") or scene.get("focus_side", "center"),
            "character_visible": beat.get("character_visible", scene.get("character_visible", False)),
            "character_role": beat.get("character_role") or scene.get("character_role", "guide"),
            "character_emotion": beat.get("character_emotion") or scene.get("emotion", "neutral"),
            "character_action": beat.get("character_action") or scene.get("character_action", "none"),
            "facial_expression": beat.get("facial_expression") or scene.get("emotion", "neutral"),
            "interaction_target": beat.get("interaction_target") or scene.get("interaction_target", ""),
            "overlay_symbols": beat.get("overlay_symbols", scene.get("overlay_symbols", [])),
            "on_screen_emphasis": beat.get("on_screen_emphasis", scene.get("on_screen_emphasis", "")),
            "top_label_text": None,
            "top_label": False,
            "camera": beat.get("camera") or scene.get("camera", "static"),
            "camera_strength": min(0.07, max(0.0, float(beat.get("camera_strength", 0.05)))),
            "duration_target": round(max(2.5, len(narration.split()) / 145 * 60), 2),
            "character_position": beat.get("character_position") or scene.get("character_position", "left"),
            "character_scale": min(.35, beat.get("character_scale", scene.get("character_scale", 0.28))),
            "visual_hierarchy": beat.get("visual_hierarchy") or f"Primary: {narration.strip(' .')[:100]}; secondary details subdued",
            "text_semantic_subject": scene.get("semantic_subject", ""),
            "text_core_claim": scene.get("core_claim", ""),
            "text_visual_message": scene.get("visual_message", ""),
            "text_visual_concept": scene.get("visual_concept", ""),
            "text_visual_objects": scene.get("visual_objects", []),
            "text_visual_relationship": scene.get("visual_relationship", ""),
        })
        beat["character_pose"] = beat.get("character_pose") or requested_pose(
            beat["character_emotion"], beat["character_action"], arch)
        beat["gaze_target"] = beat.get("gaze_target") or beat["interaction_target"] or beat["focus_object"]
        if beat["character_visible"]:
            beat["character_position"] = {"left":"right", "right":"left"}.get(beat["focus_side"],
                "left" if index % 2 == 0 else "right")
        beat["camera"] = {"question_reveal":"push_in", "cause_effect":"pan_right",
            "comparison":"pan_right", "process":"pan_right", "consequence":"push_in",
            "takeaway":"pull_out", "object_only":"static"}.get(arch, beat["camera"])
        if arch == "object_only":
            beat["camera_strength"] = .015
        beat["background_prompt"] = beat.get("background_prompt") or (
            f"Clean 2D educational illustration. Goal: {beat['story_purpose']}. "
            f"Visual archetype: {arch}. Primary focus: {beat['focus_object']} on the {beat['focus_side']}. "
            f"Hierarchy: {beat['visual_hierarchy']}. Show only this spoken idea: {narration}. "
            f"Reserve clean visual space on the {beat['character_position']} for a separately composited character. "
            "NO PEOPLE. NO HUMAN FIGURES. NO CHARACTERS. Group related objects clearly. "
            "Arrows only for process or cause and effect. No decorative connector lines, rings, floating circles, "
            "top-center labels, UI pills, or random callouts. Short labels only when attached to a relevant object and essential. "
            "Empty space is welcome. No clutter or paragraphs. "
            "Thin outlines, soft neutral palette, light background, simple shapes."
        )
        beats.append(beat)
    if len(beats) > 1:
        for beat in beats:
            if beat["visual_archetype"] in {"object_only", "process", "cause_effect", "zoom_detail"}:
                beat["character_visible"] = False
                beat["character_role"] = "none"
    for beat in beats:
        beat["overlay_symbols"] = normalize_overlays(beat["overlay_symbols"],
            beat["visual_archetype"],bool(beat["character_visible"]))
    return beats


def guard_beats(scenes: list[dict]) -> list[str]:
    warnings = []
    visible_run = 0
    last_camera = None
    camera_run = 0
    last_arch = None
    arch_run = 0
    last_pose = None
    pose_run = 0
    last_position = None
    position_run = 0
    last_prompt = None
    for scene in scenes:
        beats = scene["visual_beats"]
        for beat in beats:
            if len(beat["narration"].split()) > 22 or beat["duration_target"] > 7:
                warnings.append(f"{beat['beat_id']}: long beat")
            arch = beat["visual_archetype"]
            arch_run = arch_run + 1 if arch == last_arch else 1
            if arch_run > 3 and arch not in {"question_reveal", "takeaway"}:
                beat["visual_archetype"] = "zoom_detail"
                arch_run = 0
            last_arch = beat["visual_archetype"]
            visible_run = visible_run + 1 if beat["character_visible"] else 0
            if visible_run > 3 and beat["visual_archetype"] not in {"question_reveal", "takeaway"}:
                beat["character_visible"] = False
                beat["character_role"] = "none"
                visible_run = 0
            pose = beat["character_pose"] if beat["character_visible"] else None
            pose_run = pose_run + 1 if pose and pose == last_pose else 1
            if pose_run > 2:
                beat["character_pose"] = "questioning" if pose != "questioning" else "explaining"
                pose_run = 0
            last_pose = beat["character_pose"] if beat["character_visible"] else None
            position = beat["character_position"] if beat["character_visible"] else None
            position_run = position_run + 1 if position and position == last_position else 1
            if position_run > 2 and beat["focus_side"] == "center":
                beat["character_position"] = "right" if position == "left" else "left"
                position_run = 0
            last_position = beat["character_position"] if beat["character_visible"] else None
            camera = beat["camera"]
            camera_run = camera_run + 1 if camera == last_camera else 1
            if camera_run > 2:
                beat["camera"] = "static" if camera != "static" else "push_in"
                camera_run = 0
            last_camera = beat["camera"]
            if beat["background_prompt"] == last_prompt:
                beat["background_prompt"] += f" Vary layout: place the primary object on the {beat['focus_side']}."
                warnings.append(f"{beat['beat_id']}: repeated background prompt changed")
            last_prompt = beat["background_prompt"]
    return warnings
