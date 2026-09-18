from __future__ import annotations
import traceback
from pathlib import Path
from threading import Lock
from uuid import uuid4
from PIL import Image, ImageOps

from .config import PROJECTS_DIR, DEMO_MODE, MAX_SCENES, OPENAI_API_KEY
from .mock_service import MockService
from .render import composite_scene, render_scene, concat_scenes, write_srt
from .utils import ensure_dir, read_json, write_json, media_duration
from .visual_beats import plan_visual_beats, guard_beats
from .overlays import normalize_overlays
from .hybrid_image_engine import HybridImageEngine, prepare_image_plan

LOCK = Lock()


def make_project(payload: dict) -> tuple[str, Path]:
    project_id = uuid4().hex[:12]
    root = ensure_dir(PROJECTS_DIR / project_id)
    for name in ["images", "composited", "audio", "clips"]:
        ensure_dir(root / name)
    state = {
        "id": project_id,
        "topic": payload["topic"].strip(),
        "duration_minutes": int(payload.get("duration_minutes", 1)),
        "fps": int(payload.get("fps", 30)),
        "preferred_scene_seconds": int(payload.get("preferred_scene_seconds", 6)),
        "voice": payload.get("voice", "marin"),
        "sources": payload.get("sources") or ["web", "reddit", "news"],
        "audience": payload.get("audience", "general curious viewers"),
        "retention_level": payload.get("retention_level", "high but credible"),
        "story_mode": payload.get("story_mode", "dynamic educational storyteller"),
        "demo_mode": bool(payload.get("demo_mode", DEMO_MODE or not OPENAI_API_KEY)),
        "full_scene_mode": payload.get("full_scene_mode") is True,
        "image_cost_mode": payload.get("image_cost_mode") if payload.get("image_cost_mode") in {"low_cost","balanced","high_quality"} else "balanced",
        "ai_image_calls":0, "local_scenes":0, "image_cache_hits":0, "estimated_image_cost":0.0,
        "status": "queued", "progress": 0, "message": "Đã tạo project V3", "error": None, "scene_count": 0,
    }
    write_json(root / "state.json", state)
    return project_id, root


def update_state(root: Path, **updates):
    with LOCK:
        state = read_json(root / "state.json", {})
        state.update(updates)
        write_json(root / "state.json", state)


def choose_service(demo_mode: bool):
    if demo_mode:
        return MockService()
    from .openai_service import OpenAIService
    return OpenAIService()


def _normalize_storyboard(scenes: list[dict]) -> list[dict]:
    allowed_emotions={"curious","surprised","thinking","concerned","explaining","confident","neutral"}
    allowed_gestures={"question","react","think","point","present","warning","compare","observe","none"}
    allowed_actions={"enter","lean_in","step_back","point_at_focus","compare_sides","inspect","present","react","think","celebrate","warn","none"}
    allowed_arch={"question_reveal","cause_effect","comparison","process","zoom_detail","consequence","myth_fact","example","object_only","takeaway"}
    cameras=["zoom_in","pan_right","zoom_out","pan_left","static"]
    positions=["left","right","center"]
    visible_run=0
    for idx, scene in enumerate(scenes,1):
        scene["scene_id"]=idx
        scene.setdefault("story_purpose","explain one useful idea")
        scene.setdefault("viewer_feeling","clear")
        if scene.get("visual_archetype") not in allowed_arch: scene["visual_archetype"]="example"
        scene.setdefault("focus_object","main idea")
        scene.setdefault("focus_side","center")
        scene.setdefault("continuity_anchor","")
        scene.setdefault("character_role","guide")
        scene.setdefault("character_visible",True)
        scene.setdefault("character_position",positions[(idx-1)%len(positions)])
        scene.setdefault("character_scale",0.46)
        scene.setdefault("camera",cameras[(idx-1)%len(cameras)])
        scene.setdefault("transition","cut")
        scene.setdefault("character_action","none")
        scene.setdefault("interaction_target",scene.get("focus_object",""))
        scene.setdefault("on_screen_emphasis","")
        if scene.get("emotion") not in allowed_emotions: scene["emotion"]="neutral"
        if scene.get("gesture") not in allowed_gestures: scene["gesture"]="none"
        if scene.get("character_action") not in allowed_actions: scene["character_action"]="none"
        # Anti-template guard: adjacent scenes should not repeat the same camera+position.
        if idx>1:
            prev=scenes[idx-2]
            if scene.get("camera")==prev.get("camera") and scene.get("character_position")==prev.get("character_position"):
                scene["camera"]=cameras[(cameras.index(scene["camera"])+1)%len(cameras)] if scene["camera"] in cameras else cameras[idx%len(cameras)]
                scene["character_position"]=positions[(positions.index(scene["character_position"])+1)%len(positions)] if scene["character_position"] in positions else positions[idx%len(positions)]
        # If the model uses the character as wallpaper for too long, create an object-only beat.
        if scene.get("character_visible"):
            visible_run += 1
            if visible_run >= 4 and scene.get("character_role") not in {"reactor","demonstrator"} and scene.get("visual_archetype") not in {"question_reveal","takeaway"}:
                scene["character_visible"] = False
                scene["character_role"] = "none"
                visible_run = 0
        else:
            visible_run=0
        scene["overlay_symbols"] = normalize_overlays(scene.get("overlay_symbols",[]),
            scene["visual_archetype"],bool(scene["character_visible"]))
        # Keep emphasis short so it behaves like visual direction, not another subtitle.
        words=str(scene.get("on_screen_emphasis","")).split()
        if len(words)>4: scene["on_screen_emphasis"]=" ".join(words[:4])
        scene["novelty_key"] = f"{scene.get('visual_archetype')}|{scene.get('character_visible')}|{scene.get('character_position')}|{scene.get('camera')}"
    return scenes


def run_project(project_id: str):
    root = PROJECTS_DIR / project_id
    state = read_json(root / "state.json")
    if not state: return
    try:
        service=choose_service(state["demo_mode"])
        topic=state["topic"]; duration_minutes=state["duration_minutes"]; fps=state["fps"]
        preferred_scene_seconds=state["preferred_scene_seconds"]; voice=state["voice"]; sources=state["sources"]
        audience=state.get("audience","general curious viewers"); retention_level=state.get("retention_level","high but credible")
        max_scenes=min(MAX_SCENES,max(3,int(duration_minutes*60/max(3,preferred_scene_seconds))+3))

        update_state(root,status="research",progress=4,message="Research: tìm fact, cause/effect và những gì có thể kể bằng hình...")
        research=service.research(topic,sources); write_json(root/"research.json",research)

        update_state(root,status="audience",progress=11,message="Audience Rewrite: tìm hook, payoff và cách nói đời thường...")
        brief=service.audience_brief(topic,research,audience,retention_level); write_json(root/"audience_brief.json",brief)

        update_state(root,status="script",progress=18,message="Retention Script: viết narration ngắn, dễ hiểu, có nhịp reveal...")
        script=service.write_script(topic,research,brief,duration_minutes,audience,retention_level); write_json(root/"script.json",script)

        update_state(root,status="story",progress=25,message="Visual Story Director: thiết kế arc, motif, vai trò nhân vật và nhịp hình ảnh...")
        blueprint=service.story_blueprint(topic,research,brief,script,duration_minutes); write_json(root/"story_blueprint.json",blueprint)

        update_state(root,status="scenes",progress=32,message="Storyboard: biến từng câu thành hành động, bố cục và visual beat có mục đích...")
        scenes=service.plan_scenes(script,blueprint,preferred_scene_seconds,max_scenes)
        if not scenes: raise RuntimeError("Không tạo được scene nào.")
        scenes=_normalize_storyboard(scenes)
        for scene in scenes:
            scene["visual_beats"] = plan_visual_beats(scene)
        warnings = guard_beats(scenes)
        full_scene_mode=state.get("full_scene_mode",False)
        image_plan = prepare_image_plan(scenes,state.get("image_cost_mode","balanced"),state["demo_mode"],full_scene_mode)
        image_engine = HybridImageEngine(state.get("image_cost_mode","balanced"),state["demo_mode"],service,
                                         full_scene_mode=full_scene_mode,planned_beats=len(image_plan))
        write_json(root/"anti_static_warnings.json", warnings)
        write_json(root/"image_plan.json",image_plan)
        update_state(root,planned_ai_images=sum(item["strategy"]=="full_scene_ai" for item in image_plan),
                     **image_engine.summary())
        write_json(root/"scenes.json",scenes)
        write_json(root/"visual_beats.json",[b for s in scenes for b in s["visual_beats"]])
        write_json(root/"character_plan.json",[{"beat_id":b["beat_id"],"visible":b["character_visible"],"pose":b["character_pose"],"emotion":b["character_emotion"],"action":b["character_action"]} for s in scenes for b in s["visual_beats"]])
        write_json(root/"motion_plan.json",[{"beat_id":b["beat_id"],"camera":b["camera"],"strength":b["camera_strength"],"focus_side":b["focus_side"]} for s in scenes for b in s["visual_beats"]])
        update_state(root,scene_count=len(scenes))

        plan_index=0
        for i,scene in enumerate(scenes,1):
            progress=32+int(25*i/len(scenes)); update_state(root,status="images",progress=progress,message=f"Đang dựng visual story {i}/{len(scenes)}: {scene.get('visual_archetype','scene')}...")
            for j,beat in enumerate(scene["visual_beats"],1):
                stem=f"scene_{i:03d}_beat_{j:02d}"
                bg_path=root/"images"/f"{stem}.png"; comp_path=root/"composited"/f"{stem}.jpg"
                if not bg_path.exists():
                    image_engine.render_background(beat,bg_path,image_plan[plan_index])
                plan_index+=1
                if beat["image_strategy"]=="full_scene_ai":
                    with Image.open(bg_path) as full_scene:
                        ImageOps.fit(full_scene.convert("RGB"),(1920,1080),method=Image.Resampling.LANCZOS).save(comp_path,quality=92)
                else:
                    composite_scene(bg_path,comp_path,bool(beat["character_visible"]),beat["character_position"],float(beat["character_scale"]),
                        beat["character_emotion"],scene.get("gesture","none"),beat["overlay_symbols"],
                        character_action=beat["character_action"],focus_side=beat["focus_side"],
                        interaction_target=beat["interaction_target"],on_screen_emphasis=beat["on_screen_emphasis"],
                        visual_archetype=beat["visual_archetype"],character_pose=beat["character_pose"])
                beat["background_file"]=str(bg_path.relative_to(root)); beat["image_file"]=str(comp_path.relative_to(root))
                if j==1: scene["background_file"]=beat["background_file"]; scene["image_file"]=beat["image_file"]
            write_json(root/"scenes.json",scenes)
            write_json(root/"image_plan.json",image_plan)
            update_state(root,**image_engine.summary())

        for i,scene in enumerate(scenes,1):
            progress=57+int(19*i/len(scenes)); update_state(root,status="voice",progress=progress,message=f"TTS + timing thật {i}/{len(scenes)}...")
            audio_path=root/"audio"/f"scene_{i:03d}.wav"
            if not audio_path.exists(): service.tts(scene["narration"],audio_path,voice=voice)
            duration=media_duration(audio_path)
            if duration>120: raise RuntimeError(f"Audio scene {i} dài bất thường ({duration:.1f}s).")
            scene["duration"]=round(duration,3); scene["audio_file"]=str(audio_path.relative_to(root))
            weights=[max(1,len(b["narration"].split())) for b in scene["visual_beats"]]
            for beat,weight in zip(scene["visual_beats"],weights):
                beat["duration"]=round(duration*weight/sum(weights),3)
            write_json(root/"scenes.json",scenes)

        write_json(root/"visual_beats.json",[b for s in scenes for b in s["visual_beats"]])
        write_json(root/"motion_plan.json",[{"beat_id":b["beat_id"],"camera":b["camera"],"strength":b["camera_strength"],"focus_side":b["focus_side"],"duration":b["duration"]} for s in scenes for b in s["visual_beats"]])
        write_srt(scenes,root/"subtitles.srt")
        clips=[]
        for i,scene in enumerate(scenes,1):
            progress=76+int(21*i/len(scenes)); update_state(root,status="render",progress=progress,message=f"Render scene {i}/{len(scenes)}...")
            clip_path=root/"clips"/f"scene_{i:03d}.mp4"
            render_scene([root/b["image_file"] for b in scene["visual_beats"]],root/scene["audio_file"],clip_path,scene["duration"],fps,scene.get("camera","zoom_in"),beats=scene["visual_beats"])
            clips.append(clip_path)
        update_state(root,status="render",progress=98,message="Đang ghép video cuối..."); concat_scenes(clips,root/"output.mp4",fps)
        update_state(root,status="completed",progress=100,message="Hoàn tất V3 Visual Storyteller.",output_file="output.mp4",subtitle_file="subtitles.srt")
    except Exception as exc:
        (root/"error.log").write_text(traceback.format_exc(),encoding="utf-8"); update_state(root,status="failed",message="Pipeline bị lỗi.",error=str(exc))


def project_detail(project_id: str):
    root=PROJECTS_DIR/project_id; state=read_json(root/"state.json")
    if not state: return None
    state["research"]=read_json(root/"research.json")
    state["audience_brief"]=read_json(root/"audience_brief.json")
    state["script"]=read_json(root/"script.json")
    state["story_blueprint"]=read_json(root/"story_blueprint.json")
    state["scenes"]=read_json(root/"scenes.json",[])
    state["image_plan"]=read_json(root/"image_plan.json",[])
    return state
