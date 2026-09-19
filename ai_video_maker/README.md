# AI Visual Storyteller V3.1

## Dynamic outro

The script response now includes a separate `outro` object with `cta_angle`, `spoken_text`, `subtitle_text`, `visual_style`, `duration_sec`, and `template`. The narration keeps its normal takeaway; the CTA is recorded separately and appended after the main scenes. New projects write `outro_script.json`, `outro_plan.json`, `outro_scene.png`, `outro_audio.wav`, and `outro.mp4`. The final `output.mp4` and `subtitles.srt` include the outro.

The home page offers a dynamic or fixed outro layout and four styles: `creator_desk_mic`, `monitor_play_button`, `whiteboard_presenter`, and `cozy_creator_room`. Local character artwork is the default and does not use an image API call. Selecting AI artwork uses the existing character reference and image cache and may incur one additional image charge. Turn off **Thêm outro ngắn ở cuối video** to keep the previous output behavior. `DEFAULT_OUTRO_STYLE` in `.env` sets the fallback style.

Local outro mode uses the three supplied reference PNGs in `assets/outro/` directly: `see_you_studio.png` for creator desk and cozy room, `thanks_workspace.png` for monitor workspace, and `whiteboard_like_subscribe.png` for the board layout. The original PNG bytes are copied into each project without an image API call. The outro spoken line stays close to three short CTA patterns for general videos, habit/psychology videos, and explainers; the selected project voice records it as `outro_audio.wav`. Demo Mode uses silent mock audio.

Run `.venv\Scripts\python.exe test_outro.py` for offline script, brief, prompt, TTS, image-provider stub, and outro MP4 checks.

## Hybrid Image Engine

### Semantic visual planning

Scenes now use three explicit modes: `diagram` maps to `asset_composer`, `host` maps to `character_composite`, and `experiential` maps to `full_scene_ai`. The scene director detects lived actions and environments, carries bedroom/phone/study continuity across adjacent beats, and reserves the configured AI-image budget for the strongest moments. Experiential prompts describe the reference character's identity, action, posture, physical interaction, environment, meaningful props, mood, composition, and an optional short speech bubble. When the budget is used, the beat becomes a contextual host scene. The image model renders selected scenes; the text scene planner and local semantic director choose meaning and mode.

Run `.venv\Scripts\python.exe test_scene_director.py` for the three-mode, continuity, speech-bubble, and prompt checks. Offline reviews of saved dopamine detox and daily routine storyboards are in `projects/hybrid_test/dopamine_scene_review.json` and `projects/hybrid_test/daily_routine_scene_review.json`.

Visual beats now record `semantic_subject`, `core_claim`, `visual_message`, `visual_concept`, `visual_relationship`, `visual_objects`, `asset_match_confidence`, and `visual_novelty_score`. The planner interprets the spoken claim before choosing assets. Calendar and checklist appear only when the narration calls for a schedule or task list. Recent beats are compared for repeated assets, layout, archetype, character pose, and focus position; a third consecutive identical asset set is replanned.

The local compositor includes shape fallbacks for brain, reset cross, timeline, phone notification, habit loop, reward, environment, action, time passage, friction, urge, exercise, and conversation. `character_composite` combines these objects with the existing pose library. Selected lived experiences can use `full_scene_ai`, which edits the master character reference into a complete scene. These calls share the same AI image cap and cache as background generation. Demo Mode remains local only. The storyboard shows semantic diagnostics for each beat. An offline 77-beat dopamine detox review is saved at `projects/hybrid_test/dopamine_semantic_review.json`.

Each visual beat gets an `image_strategy` and `visual_objects` plan before rendering. Familiar objects and diagrams are composed locally with Pillow; optional transparent PNGs can be placed in `assets/routine`, `assets/study`, `assets/tech`, `assets/ui`, or `assets/misc`. Missing PNGs use built-in shapes. Complex metaphors can use OpenAI image generation. The character is composited afterward from the local pose library, so background requests do not include the character reference.

The home page offers Low Cost, Balanced, and High Quality image modes. Their AI image limits are 2, 6, and 8 respectively, subject to `MAX_AI_IMAGES_PER_PROJECT` (default 6). Demo Mode uses only local images. OpenAI backgrounds use `gpt-image-1-mini` by default, with quality based on the selected mode. Matching prompts reuse `cache/images` without another API call. Provider failures and exhausted image budgets fall back to local composition.

Balanced mode selects up to 30% of short-video beats for integrated AI scenes while respecting the six-image cap. Claim-specific visual checks repair known object mismatches before render. The storyboard shows a 0–1 visual quality score; scores below 0.55 are flagged for review. These scores are planning estimates, not an assessment of generated image pixels.

Enable **Tạo ảnh AI toàn cảnh cho toàn bộ video** to request an integrated character illustration for every visual beat. This mode uses the selected image quality, retains cache reuse, and sets the per-project image limit to the actual beat count. It requires an API key with Demo Mode off. A three-minute project may make dozens of paid image requests; inspect the beat count and image plan before choosing this mode. The prompt limits each scene to one focal object and at most two quiet background objects. If an image request fails, the existing local fallback is recorded in the image plan.

Each project writes `image_plan.json`; the project page shows LOCAL/AI badges, AI call and local scene counts, cache hits, and an approximate image cost. The estimate covers generated images only and can be adjusted in `.env` with `IMAGE_COST_LOW_USD`, `IMAGE_COST_MEDIUM_USD`, and `IMAGE_COST_HIGH_USD`.

Run `.venv\Scripts\python.exe test_hybrid.py` for planner, cache, cap, and fallback checks. Run `.venv\Scripts\python.exe test_smoke.py` for the existing compositing and motion checks.

## Run V3.1

On Windows, run `start_windows.bat` from this directory, or run `.venv\Scripts\python.exe app.py` and open `http://127.0.0.1:5000`. Select Demo Mode to run without API calls. For a fresh environment, create a virtual environment and install `requirements.txt` first.

Each scene now contains `visual_beats`. Long narration is split into separate images and camera moves, while TTS remains per scene. Generated projects include `visual_beats.json`, `character_plan.json`, `motion_plan.json`, and `anti_static_warnings.json`. Optional character pose PNGs go in `assets/character/poses/`; missing poses fall back to `main.png`.

The Character Pose Library on the home page shows installed poses. With an API key configured, **Generate Missing Poses** creates only absent files; each installed pose also has an explicit **Regenerate Pose** button. The generator edits the master character reference into a transparent PNG. Generation uses the OpenAI image API and may take time and incur API charges. Demo Mode uses installed pose assets and needs no API call.

Visual overlays are now opt-in. The compositor no longer adds automatic yellow focus rings or top-center label pills. Beats record `overlay_symbols`, `top_label: false`, and `top_label_text: null` for inspection. Supported marks are question, exclamation, check, warning, short arrow, small highlight, underline, and spark; unsupported decorative marks are ignored.

Run `.venv\Scripts\python.exe test_smoke.py` to check compositing, SRT output, and a two-beat motion render.

V3 chuyển project từ **AI slideshow/explainer** sang **AI visual storyteller**.

## “AI visual storyteller” là gì?

Không phải: “câu này nói về RAM → tạo một ảnh RAM”.

Mà là: trước mỗi scene, AI phải trả lời:

1. Scene này tồn tại để làm gì trong câu chuyện?
2. Người xem cần cảm thấy/tò mò/hiểu điều gì sau scene này?
3. Hình ảnh nào tự kể được ý đó ngay cả khi tắt tiếng?
4. Nhân vật có thật sự cần xuất hiện không?
5. Nếu có, nhân vật đang **làm gì với nội dung**: phản ứng, chỉ, so sánh, quan sát, cảnh báo, trình bày?
6. Scene này khác scene trước ở bố cục/camera/archetype như thế nào?

Ví dụ topic “Why is RAM expensive?”:

```text
Scene 1 — HOOK / question_reveal
Nhân vật ngạc nhiên trước price tag RAM tăng → dấu ? → zoom in

Scene 2 — REVEAL / comparison
Hai phía: consumer RAM vs AI/data-center demand → nhân vật đứng giữa so sánh

Scene 3 — CAUSE / cause_effect
Object-only: nhà máy memory → mũi tên → AI/server memory

Scene 4 — CONSEQUENCE / zoom_detail
Ít hộp consumer RAM hơn ở phía người mua → spotlight vào “less supply”

Scene 5 — TAKEAWAY
Nhân vật quay lại, trình bày 1 lời khuyên cụ thể
```

Đó là **visual storytelling**: hình ảnh có nhịp, có nguyên nhân-kết quả và có diễn xuất, thay vì nhân vật đứng cạnh một background ngẫu nhiên.

## Pipeline V3

```text
Keyword
→ Research
→ Audience Rewrite
→ Retention Script
→ Visual Story Blueprint
→ Shot-by-shot Storyboard
→ Anti-template / repetition guard
→ Background generation
→ Character acting + interaction overlays
→ TTS + duration thật
→ Short subtitles
→ Camera movement
→ MP4
```

## Những điểm mới so với V2

- `story_blueprint.json`: arc, opening tension, story promise, continuity anchors, visual motif.
- Mỗi scene có `story_purpose`, `viewer_feeling`, `visual_archetype`, `focus_object`, `focus_side`.
- Nhân vật có `character_role`, `character_action`, `interaction_target`; không mặc định đứng trong mọi scene.
- Hỗ trợ scene `object_only` để đồ vật/cause-effect tự kể chuyện.
- Anti-template guard đổi camera/vị trí nếu scene liền nhau quá giống; sau nhiều scene nhân vật liên tục có thể chuyển sang object-only beat.
- Overlay mới: bracket, spotlight, interaction arrow và short emphasis label.
- UI hiện Purpose / Focus / Action cho từng scene để bạn nhìn được “đạo diễn” của AI.

## Chạy Windows

1. Giải nén ZIP.
2. Double-click `start_windows.bat`.
3. Mở `http://127.0.0.1:5000`.
4. Test Demo Mode trước.
5. Dùng API thật: copy `.env.example` → `.env`, điền `OPENAI_API_KEY`, bỏ tick Demo Mode.

## Nhân vật

Ảnh gốc: `assets/character/main.png`.

V3 vẫn bảo toàn nhân vật gốc và có fallback acting bằng transform/overlay. Nếu bạn thêm pose PNG thật vào `assets/character/poses/`, renderer sẽ ưu tiên ảnh pose trùng emotion.

## Output

- `research.json`
- `audience_brief.json`
- `script.json`
- `story_blueprint.json`
- `scenes.json`
- `subtitles.srt`
- `output.mp4`

## Lưu ý quan trọng

V3 giúp video bớt cảm giác template/mass-produced, nhưng không có công cụ nào có thể bảo đảm YouTube sẽ chấp thuận kiếm tiền. Nội dung vẫn cần có giá trị riêng, fact-check, cách giải thích hữu ích và sự khác biệt thật giữa các video.
