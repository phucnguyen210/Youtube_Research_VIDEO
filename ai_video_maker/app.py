from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from flask import Flask, jsonify, render_template, request, send_from_directory

from core.config import PROJECTS_DIR, DEMO_MODE, OPENAI_API_KEY
from core.pipeline import make_project, project_detail, run_project
from core.character_pose_selector import POSE_NAMES, pose_status
from core.character_pose_generator import generate_pose, generate_missing
from core.config import ASSETS_DIR
from core.outro import REFERENCE_OUTROS

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)
pose_lock = Lock()
pose_job = {"status":"idle", "message":""}


def _run_pose_job(name: str | None, overwrite: bool):
    try:
        if name:
            generate_pose(name, overwrite=overwrite)
            message=f"Generated {name}"
        else:
            made=generate_missing()
            message=f"Generated {len(made)} missing poses"
        pose_job.update(status="completed",message=message)
    except Exception as exc:
        pose_job.update(status="failed",message=str(exc))

@app.get("/")
def home():
    return render_template("index.html", default_demo=DEMO_MODE or not bool(OPENAI_API_KEY), api_configured=bool(OPENAI_API_KEY))

@app.post("/api/projects")
def create_project():
    payload=request.get_json(force=True); topic=(payload.get("topic") or "").strip()
    if not topic: return jsonify({"error":"Bạn chưa nhập keyword/topic."}),400
    duration=int(payload.get("duration_minutes",1)); fps=int(payload.get("fps",30)); scene_s=int(payload.get("preferred_scene_seconds",6))
    if duration not in {1,3,5,10}: return jsonify({"error":"Thời lượng không hợp lệ."}),400
    if fps not in {24,30,60}: return jsonify({"error":"FPS không hợp lệ."}),400
    if scene_s not in {4,6,8}: return jsonify({"error":"Scene length không hợp lệ."}),400
    if payload.get("full_scene_mode") is True and (payload.get("demo_mode") or DEMO_MODE or not OPENAI_API_KEY):
        return jsonify({"error":"Full-scene mode requires an API key and Demo Mode off."}),400
    project_id,_=make_project(payload); executor.submit(run_project,project_id); return jsonify({"project_id":project_id})

@app.get("/api/projects/<project_id>")
def get_project(project_id):
    detail=project_detail(project_id)
    if not detail: return jsonify({"error":"Không tìm thấy project."}),404
    return jsonify(detail)

@app.get("/projects/<project_id>/<path:filename>")
def project_file(project_id,filename):
    root=(PROJECTS_DIR/project_id).resolve(); candidate=(root/filename).resolve()
    if root not in candidate.parents and candidate!=root: return jsonify({"error":"Invalid path"}),400
    return send_from_directory(root,filename,as_attachment=filename.endswith((".mp4",".srt",".json",".log")))

@app.get("/api/health")
def health():
    return jsonify({"ok":True,"api_configured":bool(OPENAI_API_KEY),"default_demo":DEMO_MODE or not bool(OPENAI_API_KEY),"version":"3.1"})

@app.get("/api/poses")
def get_poses():
    return jsonify({"poses":pose_status(),"job":dict(pose_job),"api_configured":bool(OPENAI_API_KEY)})

@app.post("/api/poses/generate")
def start_pose_generation():
    payload=request.get_json(silent=True) or {}
    name=payload.get("name")
    if name is not None and name not in POSE_NAMES:
        return jsonify({"error":"Unknown pose"}),400
    if not OPENAI_API_KEY:
        return jsonify({"error":"OPENAI_API_KEY is required to generate poses"}),400
    overwrite=bool(payload.get("overwrite",False))
    with pose_lock:
        if pose_job["status"]=="running":
            return jsonify({"error":"Pose generation is already running"}),409
        pose_job.update(status="running",message="Generating poses...")
        executor.submit(_run_pose_job,name,overwrite)
    return jsonify({"ok":True}),202

@app.get("/assets/character/poses/<name>.png")
def pose_image(name):
    if name not in POSE_NAMES:
        return jsonify({"error":"Unknown pose"}),404
    return send_from_directory(ASSETS_DIR/"character"/"poses",f"{name}.png")

@app.get("/assets/outro/<name>.png")
def outro_reference_image(name):
    filename=f"{name}.png"
    if filename not in set(REFERENCE_OUTROS.values()):
        return jsonify({"error":"Unknown outro image"}),404
    return send_from_directory(ASSETS_DIR/"outro",filename)

if __name__=="__main__": app.run(host="127.0.0.1",port=5000,debug=False,threaded=True)
