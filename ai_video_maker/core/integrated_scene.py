"""Prompt only for selected full-scene illustrations."""
from __future__ import annotations

CHARACTER_IDENTITY=("same young male cartoon character as the supplied reference: short black hair, "
                    "warm light skin, pale mint-green shirt, dark charcoal pants, black shoes, "
                    "simple black outlines and the same face proportions")

def build_integrated_scene_prompt(beat: dict) -> str:
    minimal=bool(beat.get("full_scene_mode"))
    props=list(dict.fromkeys(str(x) for x in beat.get("supporting_objects",[]) if x))[:3 if minimal else 8]
    bubble=str(beat.get("speech_bubble_text","")).strip()[:55]
    bubble_rule=(f'One short speech bubble with exactly: "{bubble}".' if bubble
                 else "No speech bubble or other text.")
    density_rule=("Keep the room extremely simple: one character, one focal object, and at most two quiet background objects. Large calm areas and uncluttered framing. Do not add props merely because they appear in the narration."
                  if minimal else "Show 3-8 supporting objects only when they make the situation clear.")
    return f"""Create a clean, expressive 2D cartoon story illustration for a 16:9 educational video.
Use the supplied character reference. Preserve {CHARACTER_IDENTITY}.
This is one lived moment. Draw the character inside the environment, with feet or seated body grounded on the same floor and perspective as the furniture. Objects should be placed where the action uses them.
Visual style: warm cream background, restrained mint-green and muted brown accents, thin dark hand-drawn outlines, simple readable face, subtle paper texture. Match the quiet close-up cartoon look of the character reference. Avoid detailed room decoration.

Scene meaning: {beat.get('visual_message','')}
Spoken moment: {beat.get('narration','')}
Character body action: {beat.get('character_action_description','')}
Facial emotion: {beat.get('emotion_description','')}
Posture: {beat.get('body_posture_description','')}
Physical interaction: {beat.get('object_interaction_description','')}
Environment: {beat.get('environment','')}
Continuity group: {beat.get('continuity_group') or 'standalone'}; keep location and props consistent with nearby beats in this group.
Meaningful supporting objects: {', '.join(props)}.
Composition: {beat.get('composition_template','integrated_room')}; one clear action and readable face, with the character naturally grounded in the scene. Keep the character, face, hands, and key props within the central 16:9 safe area so a small top/bottom crop preserves them.
Cause and effect: the character's pose, gaze, hands, and touched object must make the spoken action visible without a caption. Use foreground, middle ground, and background only where they clarify place and action. Maintain the same room and prop positions across this continuity group.
Mood: {beat.get('viewer_feeling') or beat.get('emotion_description','')}; soft muted colors, off-white or light gray surfaces, expressive line art.
{bubble_rule}
{density_rule} Avoid isolated icons, visual clutter, extra people, floating top labels, decorative circles, logos, 3D, and photorealism.""".strip()
