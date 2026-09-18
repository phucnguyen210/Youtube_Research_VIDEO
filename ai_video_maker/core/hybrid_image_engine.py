"""Per-project image planning, budget enforcement, cache, and fallback."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .asset_composer import compose_assets
from .config import (CACHE_IMAGES_DIR, IMAGE_PROVIDER, IMAGE_MODEL, IMAGE_QUALITY, CHARACTER_PATH,
                     IMAGE_COST_ESTIMATE, MAX_AI_IMAGES_PER_PROJECT, VISUAL_STYLE)
from .image_cache import cache_key, get_or_generate
from .image_strategy import MODE_QUALITY, mode_limit, plan_visual_objects, select_image_strategy
from .visual_repetition_guard import guard_visual_repetition
from .scene_director import direct_beat, assign_continuity, allocate_experiential_budget, FULL_SCENE_CONCEPTS
from .integrated_scene import build_integrated_scene_prompt
from .visual_quality import audit_visual

AI_SIZE = "1536x1024"
STYLE_ID = hashlib.sha256(VISUAL_STYLE.encode("utf-8")).hexdigest()[:16]


def prepare_image_plan(scenes: list[dict], mode: str, demo_mode: bool,
                       full_scene_mode: bool = False) -> list[dict]:
    beats=[beat for scene in scenes for beat in scene["visual_beats"]]
    for beat in beats:
        beat["visual_objects"] = plan_visual_objects(beat)
        direct_beat(beat)
    assign_continuity(beats)
    if full_scene_mode and not demo_mode:
        for beat in beats:
            was_diagram = beat["scene_mode"] == "diagram"
            beat["scene_mode"] = "experiential"
            beat["character_visible"] = True
            beat["composition_template"] = "minimal integrated story illustration"
            beat["supporting_objects"] = list(dict.fromkeys(
                obj["type"] for obj in beat.get("visual_objects", [])
                if obj.get("type") not in {"idea", "action", "person"}))[:3]
            if was_diagram:
                environment, action, emotion = FULL_SCENE_CONCEPTS.get(
                    beat.get("visual_concept"),
                    ("quiet, simple room", "looking at one concrete object that explains the spoken idea", "thoughtful"))
                beat["environment"] = environment
                beat["character_action_description"] = action
                beat["emotion_description"] = emotion
            beat["full_scene_mode"] = True
    else:
        cap = 0 if demo_mode else mode_limit(mode,MAX_AI_IMAGES_PER_PROJECT)
        if mode == "balanced":
            cap = min(cap, max(3, round(len(beats) * .30)))
        allocate_experiential_budget(beats,cap)
    guard_visual_repetition(beats)
    for beat in beats:
        audit_visual(beat)
        if beat.get("full_scene_mode"):
            beat["supporting_objects"] = list(dict.fromkeys(
                obj["type"] for obj in beat.get("visual_objects", [])
                if obj.get("type") not in {"idea", "action", "person"}))[:3]
    plan=[]
    for beat in beats:
            strategy,reason = select_image_strategy(beat,mode,demo_mode)
            beat["image_strategy"] = strategy
            beat["image_strategy_reason"] = reason
            plan.append({"beat_id":beat["beat_id"],"strategy":strategy,"reason":reason,
                         "visual_objects":beat["visual_objects"],"visual_message":beat["visual_message"],
                         "visual_concept":beat["visual_concept"],
                         "scene_mode":beat["scene_mode"],"environment":beat["environment"],
                         "continuity_group":beat["continuity_group"],
                         "asset_match_confidence":beat["asset_match_confidence"],
                         "visual_novelty_score":beat["visual_novelty_score"],
                         "visual_quality_score":beat["visual_quality_score"],
                         "semantic_mismatch":beat["semantic_mismatch"],
                         "visual_quality_warning":beat["visual_quality_warning"],"cache_hit":False})
    return plan


class HybridImageEngine:
    def __init__(self, mode: str, demo_mode: bool, service, *, cache_dir: Path = CACHE_IMAGES_DIR,
                 global_limit: int = MAX_AI_IMAGES_PER_PROJECT,
                 full_scene_mode: bool = False, planned_beats: int = 0):
        self.mode = mode if mode in MODE_QUALITY else "balanced"
        self.demo_mode = demo_mode
        self.service = service
        self.cache_dir = cache_dir
        self.limit = planned_beats if full_scene_mode and not demo_mode else mode_limit(self.mode,global_limit)
        self.quality = MODE_QUALITY[self.mode]
        if self.mode == "balanced" and IMAGE_QUALITY in IMAGE_COST_ESTIMATE:
            self.quality = IMAGE_QUALITY
        self.ai_image_calls=0
        self.local_scenes=0
        self.cache_hits=0
        self.estimated_image_cost=0.0

    def render_background(self, beat: dict, output_path: Path, plan_entry: dict) -> None:
        strategy=beat["image_strategy"]
        reason=beat["image_strategy_reason"]
        if strategy=="full_scene_ai":
            prompt=build_integrated_scene_prompt(beat)
            ref_id=hashlib.sha256(CHARACTER_PATH.read_bytes()).hexdigest()[:16] if CHARACTER_PATH.is_file() else "missing"
            style_id=f"{STYLE_ID}-full-{ref_id}"
        else:
            prompt=(f"{beat['background_prompt']}\nVisual message: {beat['visual_message']}\n"
                    "NO PEOPLE. NO HUMAN FIGURES. NO CHARACTERS. "
                    f"Leave clean space on the {beat.get('character_position', 'left')} "
                    "for the separately composited character.")
            style_id=STYLE_ID
        cached=self.cache_dir/f"{cache_key(prompt,IMAGE_MODEL,self.quality,AI_SIZE,style_id)}.png"
        if strategy in {"ai_image","full_scene_ai"} and self.ai_image_calls>=self.limit and not cached.is_file():
            strategy="character_composite" if strategy=="full_scene_ai" else "asset_composer"
            beat["scene_mode"]="host" if strategy=="character_composite" else "diagram"
            reason=f"AI image cap ({self.limit}) reached; local fallback"
        if strategy in {"ai_image","full_scene_ai"} and IMAGE_PROVIDER!="openai":
            strategy="character_composite" if strategy=="full_scene_ai" else "asset_composer"
            beat["scene_mode"]="host" if strategy=="character_composite" else "diagram"
            reason=f"Image provider '{IMAGE_PROVIDER}' is unavailable; local fallback"
        if strategy in {"ai_image","full_scene_ai"}:
            try:
                def generate(path):
                    self.ai_image_calls+=1
                    if strategy=="full_scene_ai":
                        self.service.generate_full_scene(prompt,path,quality=self.quality,size=AI_SIZE)
                    else:
                        self.service.generate_background(prompt,path,quality=self.quality,size=AI_SIZE)
                    self.estimated_image_cost+=IMAGE_COST_ESTIMATE.get(self.quality,0.015)
                called=get_or_generate(self.cache_dir,output_path,prompt,IMAGE_MODEL,self.quality,
                                       AI_SIZE,style_id,generate)
                if not called:
                    self.cache_hits+=1
                    plan_entry["cache_hit"]=True
                    reason="reused cached AI background"
            except Exception as exc:
                strategy="character_composite" if strategy=="full_scene_ai" else "asset_composer"
                beat["scene_mode"]="host" if strategy=="character_composite" else "diagram"
                reason=f"AI image failed ({type(exc).__name__}); local fallback"
                plan_entry["error"]=str(exc)[:200]
        if strategy in {"asset_composer","character_composite"}:
            compose_assets(beat,output_path)
            self.local_scenes+=1
        beat["image_strategy"]=strategy
        beat["image_strategy_reason"]=reason
        plan_entry["strategy"]=strategy
        plan_entry["reason"]=reason
        plan_entry["scene_mode"]=beat["scene_mode"]

    def summary(self) -> dict:
        return {"ai_image_calls":self.ai_image_calls,"local_scenes":self.local_scenes,
                "image_cache_hits":self.cache_hits,
                "estimated_image_cost":round(self.estimated_image_cost,4),
                "image_cost_currency":"USD", "image_quality":self.quality,
                "max_ai_images":self.limit}
