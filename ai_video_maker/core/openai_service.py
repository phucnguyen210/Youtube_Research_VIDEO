from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

from openai import OpenAI

from .config import (
    OPENAI_API_KEY, TEXT_MODEL, IMAGE_MODEL, IMAGE_QUALITY, TTS_MODEL, TTS_VOICE,
    VISUAL_STYLE, SCRIPT_RULES, STORY_RULES, CHARACTER_PATH,
)
from .utils import extract_json
from .image_provider import OpenAIImageProvider
from .outro import normalize_outro, plan_outro_scene as build_outro_scene


class OpenAIService:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY chÆ°a Ä‘Æ°á»£c cáº¥u hÃ¬nh trong file .env")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.image_provider = OpenAIImageProvider(self.client)

    @staticmethod
    def _duration_strategy(duration_minutes: int) -> str:
        """Return continuous, duration-aware editorial guidance for any video length."""
        if duration_minutes <= 2:
            return """
ULTRA-SHORT EXPLAINER (up to 2 minutes):
- Deliver one central answer, supported by 2-3 essential points.
- Hook in the first 3-5 seconds and pay it off immediately.
- Use one vivid example at most; remove history, side paths, and secondary advice.
- Create a meaningful turn every 15-25 seconds without sounding frantic.
- Use one continuous arc: problem -> explanation -> action.
- Reserve roughly the final 10 seconds for one memorable action or conclusion.
""".strip()
        if duration_minutes <= 5:
            return """
SHORT YOUTUBE EXPLAINER (3-5 minutes):
- Build around one clear transformation and 3-5 memorable ideas.
- Hook in the first 5-8 seconds; reframe the problem within the first 20 seconds.
- Use a question, contrast, micro-example, reveal, or useful action about every 20-35 seconds.
- Include 1-2 concrete examples the viewer can picture and copy.
- Use one continuous arc with smooth transitions rather than formal chapters.
- Reserve roughly the final 15-20 seconds for one rule and one immediate action.
""".strip()
        if duration_minutes <= 10:
            return """
STANDARD YOUTUBE EXPLAINER (6-10 minutes):
- Organize the argument into 4-6 connected sections, each answering a distinct sub-question.
- Hook in the first 5-10 seconds; establish the stakes and roadmap within 30-45 seconds.
- Add a meaningful retention beat about every 35-60 seconds.
- Introduce a larger question, reveal, or perspective shift every 2-3 minutes.
- Use 2-4 grounded examples, comparisons, or short scenarios.
- Develop each important point before moving on; do not create artificial speed.
- Reserve roughly the final 30-45 seconds to synthesize the lesson and give a practical next step.
""".strip()
        if duration_minutes <= 20:
            return """
EXTENDED YOUTUBE EXPLAINER (11-20 minutes):
- Organize the script into 5-8 substantial chapters that advance one central argument.
- Open with a compelling problem and payoff, then establish a clear narrative roadmap within the first minute.
- Use micro-retention beats about every 45-75 seconds and a major reveal, question, case study, or perspective shift every 3-4 minutes.
- Use multiple grounded examples and explain important mechanisms in enough depth to justify the runtime.
- Vary modes across chapters: explanation, comparison, case, consequence, objection, and application.
- Create callbacks between chapters so the video feels like one story, not separate essays.
- Include a midpoint escalation: a deeper cause, exception, consequence, or surprising connection.
- Reserve roughly the final 45-60 seconds to synthesize the complete argument and give practical next steps.
""".strip()
        if duration_minutes <= 30:
            return """
LONG-FORM YOUTUBE EXPLAINER (21-30 minutes):
- Build 6-10 substantial chapters around a clear thesis, with each chapter earning its runtime.
- Establish the central tension, payoff, and roadmap within the first 60-90 seconds.
- Use subtle micro-retention beats about every 60-90 seconds and a major narrative turn every 4-6 minutes.
- Combine mechanisms, case studies, objections, exceptions, consequences, and practical applications.
- Give complex ideas room to breathe; retention must come from progression and clarity, not constant teasing.
- Use recurring questions, motifs, or examples as callbacks across the script.
- Include at least one meaningful counterargument or limitation when supported by the research.
- Build toward a final synthesis rather than merely repeating earlier points.
- Reserve roughly the final 60-90 seconds for synthesis, implications, and an actionable conclusion.
""".strip()
        return """
DEEP-DIVE YOUTUBE VIDEO (over 30 minutes):
- Design a documentary-style hierarchy: 3-5 major acts, each containing 2-4 focused chapters.
- Give every act its own question and payoff while advancing one central thesis.
- Establish the central tension, viewer payoff, and high-level roadmap within the first 90 seconds.
- Use subtle micro-retention beats about every 60-120 seconds and a major act-level turn every 5-8 minutes.
- Alternate explanation, evidence, case study, counterargument, consequence, and application to prevent monotony.
- Use several grounded case studies or extended examples, but only when each reveals something new.
- Add callbacks and transitions between acts so the narration remains one coherent story.
- Address uncertainty, limitations, competing explanations, and exceptions when the research supports them.
- Retention must come from accumulating understanding, not repeated hooks or manufactured suspense.
- End each act with a resolved question and the next logical question, never with empty clickbait.
- Reserve roughly the final 90-150 seconds for synthesis, implications, and clear practical takeaways.
""".strip()

    def research(self, topic: str, sources: Iterable[str]) -> dict:
        source_notes = []
        sources = set(sources)
        if "reddit" in sources:
            source_notes.append("Search Reddit for recurring firsthand experiences and objections; anecdotes are not proof.")
        if "x" in sources:
            source_notes.append("Search public X/Twitter pages when accessible for current examples and reactions.")
        if "voz" in sources:
            source_notes.append("Search VOZ (voz.vn) when relevant for Vietnamese community perspectives.")
        if "news" in sources:
            source_notes.append("Search reputable news/reporting and trace important claims toward primary sources when possible.")
        if "web" in sources or not source_notes:
            source_notes.append("Search the broader web, prioritizing primary, reputable and recent sources.")

        prompt = f"""
You are the research layer for an educational visual-storytelling video.
Topic: {topic}

Research instructions:
- {' '.join(source_notes)}
- Collect only facts that directly help answer the viewer's likely question.
- Separate strong factual support from opinions/anecdotes.
- Deduplicate repeated claims.
- Prefer concrete cause/effect explanations and practical implications.
- Flag jargon that should be translated into plain English.
- Identify concrete objects, systems, timelines, comparisons or consequences that could be shown visually.
- Identify recurring everyday BEHAVIORS, HABITS, TRIGGERS, and MICRO-MOMENTS that make the topic feel personally familiar to the target viewer (for example: reaching for the phone while waiting, watching something while eating, checking notifications during a quiet moment). Only include behaviors that are plausible from the supplied sources; do not present anecdotes as universal facts.
- Separate a behavior viewers may recognize from a factual claim about why that behavior happens. The script may use the behavior as a mirror, but causal explanations still need research support.
- Prefer concrete "you can picture it" moments over abstract labels when both are equally supported.
- Do not invent a source, statistic, URL, quote, or consensus.

Return ONLY valid JSON:
{{
  "topic": "...",
  "one_sentence_answer": "...",
  "key_points": [
    {{
      "point": "...",
      "why_it_matters": "...",
      "plain_english": "...",
      "visualizable_as": ["object", "cause_effect", "comparison", "timeline", "before_after", "example"],
      "confidence": "high|medium|low",
      "source_urls": ["https://..."]
    }}
  ],
  "jargon_to_translate": [{{"term":"...","plain_english":"..."}}],
  "sources": [
    {{"title":"...","url":"https://...","platform":"web|reddit|x|news|voz|other","why_useful":"..."}}
  ]
}}
""".strip()
        response = self.client.responses.create(
            model=TEXT_MODEL,
            tools=[{"type": "web_search", "search_context_size": "high"}],
            input=prompt,
        )
        return extract_json(response.output_text)

    def audience_brief(self, topic: str, research: dict, audience: str, retention_level: str) -> dict:
        prompt = f"""
Turn research into a viewer-retention brief WITHOUT adding new facts.
Topic: {topic}
Audience: {audience}
Retention style: {retention_level}

Research JSON:
{json.dumps(research, ensure_ascii=False)}

Rules:
- Identify what a curious non-expert wants answered first.
- Find the simplest surprising contrast, consequence, or misconception supported by research.
- Translate jargon into everyday language.
- Do not sensationalize beyond the evidence.
- Build curiosity gaps that are paid off within the video, not empty clickbait.
- Design hooks for spoken YouTube narration, not article introductions.
- A strong hook should expose a familiar pain, overturn a believable assumption, and promise a concrete payoff.
- Build a VIEWER-MIRROR bank: specific ordinary moments that make the viewer think "I do that" or "I've been there" before the explanation begins. Prefer tiny behaviors over broad statements about personality.
- Good mirror moments are situational and visible: waiting at a red light and instinctively reaching for the phone; eating while needing a video on; opening an app during a 30-second pause; turning on something in the background because silence feels uncomfortable.
- Do not claim that every viewer does these things. Phrase them as recognizable possibilities, questions, or scenes: "Ever notice...?", "Maybe you do this too...", "Think about the last time...". Avoid repeating the same verbal formula across videos.
- The mirror must connect directly to the topic and create a reason to keep watching. Do not add random relatable anecdotes merely for emotion.
- After recognition, create a small tension: reveal what the behavior may be costing, hiding, or preventing, then promise the useful payoff grounded in the research.
- Do not begin with a greeting, channel introduction, topic definition, or "In this video".
- Identify several evidence-supported questions, contrasts, examples, reveals, and useful actions that the script writer can select according to runtime.
- Keep this brief duration-neutral. The script-writing stage will choose the correct depth, number of sections, and retention cadence.

Return ONLY JSON:
{{
  "viewer_question": "...",
  "viewer_mirror_moments": [
    {{"scene":"specific behavior the viewer may recognize","hidden_tension":"what makes it interesting","bridge_to_topic":"how it naturally leads into the subject"}}
  ],
  "recognition_hook_options": ["behavior-first hook", "behavior-first hook", "behavior-first hook"],
  "hook_options": ["...", "...", "..."],
  "recommended_hook": "the strongest hook and why it fits the evidence",
  "core_payoff": "...",
  "simple_explanations": ["..."],
  "avoid_or_translate": ["..."],
  "curiosity_beats": ["question", "small reveal", "bigger cause", "consequence", "takeaway"],
  "retention_assets": [
    {{"type": "question|contrast|example|reveal|objection|action", "idea": "...", "payoff": "..."}}
  ],
  "recommended_opening_pattern": ["viewer_mirror", "pattern_interrupt", "topic_reveal", "payoff"],
  "recommended_structure": ["viewer_mirror", "hook", "context", "cause", "why_it_matters", "takeaway"]
}}
""".strip()
        response = self.client.responses.create(model=TEXT_MODEL, input=prompt)
        return extract_json(response.output_text)

    def write_script(self, topic: str, research: dict, audience_brief: dict,
                     duration_minutes: int, audience: str, retention_level: str) -> dict:
        duration_minutes = max(1, int(duration_minutes))
        target_words = max(95, int(duration_minutes * 145))
        duration_strategy = self._duration_strategy(duration_minutes)
        max_output_tokens = min(30000, max(2500, int(target_words * 2.0)))
        routine_scenarios=("For a student daily-routine topic, organize the narration as a realistic day, "
                           "not a disconnected list of study tips. Open with a familiar failed-routine moment, "
                           "then explain that the solution is a few flexible anchors rather than a rigid perfect schedule. "
                           "Select and develop the strongest research-grounded anchors according to the duration strategy, such as sleep, "
                           "specific planning, active recall or spaced review, movement/breaks, phone friction, "
                           "and a short shutdown routine. For a short video, use one compact sample day; for a standard video, "
                           "use a fuller day; for long-form, compare realistic schedules or student constraints only when supported. "
                           "Make clear that exact clock times depend on age, classes, commute, health, energy, and responsibilities. "
                           "Do not prescribe an unsupported universal wake-up time, meal rule, study timer, or health claim."
                           if "routine" in topic.lower() and "student" in topic.lower() else "")
        prompt = f"""
Write an English narration script for a highly understandable educational explainer.
Topic: {topic}
Audience: {audience}
Target duration: {duration_minutes} minute(s), about {target_words} spoken words.
Retention style: {retention_level}

Grounding research:
{json.dumps(research, ensure_ascii=False)}

Audience/retention brief:
{json.dumps(audience_brief, ensure_ascii=False)}

Writing rules:
{SCRIPT_RULES}

Duration-specific editorial strategy:
{duration_strategy}

Additional rules:
- Write for YouTube retention, while staying fully grounded in the supplied research.
- The first 5-8 seconds must contain: (1) a familiar viewer pain or surprising contrast, and (2) a specific payoff.
- BEFORE or WITHIN that hook, use a RECOGNITION-FIRST cold open when the topic supports it: show one or more tiny, concrete behaviors the viewer may have done themselves. The goal is the feeling "that's me" before giving advice or explanation.
- Mirror behavior, not identity. Describe what someone DOES in a moment, not what kind of person they ARE.
- Examples of the desired style (adapt to the topic; do not copy mechanically): "You stop at a red light and your hand is already reaching for your phone." / "You sit down to eat, and before the first bite, a video is already playing." / "A quiet 30 seconds appears, and somehow an app is open before you even decided to check it."
- Use only behavior examples that fit the research/topic. Do not imply prevalence unless the research supports it.
- After 1-4 mirror moments (depending on runtime), pivot quickly from recognition -> hidden pattern/problem -> concrete payoff. The opening must MOVE, not linger in a montage of relatable examples.
- For ultra-short videos use 1-2 mirror moments; 3-5 minute videos usually use 2-3; 6-10 minute videos may use 2-4; long-form may return to the same viewer behavior as a callback later rather than stuffing more examples into the opening.
- Do not start by giving the solution. Let the viewer first recognize the pattern, then explain why it matters, then earn the advice.
- Never open with "Hi", "Welcome", "Today we're going to", "In this video", a dictionary definition, or broad background.
- The hook must be honest: no fearmongering, fake urgency, unsupported certainty, or promise the script does not pay off.
- Set the JSON field "hook" to the exact opening words of the narration. The narration MUST begin with that hook verbatim; do not keep the hook separate from the spoken script.
- Follow the timing, section count, example depth, and retention cadence in the duration-specific strategy above.
- Scale the number of ideas to the runtime. Never force a short-video structure onto a long video or pad a short video with long-form context.
- Retention beats may use a question, contrast, micro-example, reveal, objection, callback, consequence, or useful action. Do not announce them or use them mechanically.
- Use an open loop only when its answer is delivered later in this same script.
- Make each section earn its place: new information, a clearer example, or a practical consequence. Remove repetition and motivational filler.
- Use the number of ideas and examples specified by the duration strategy. Connect them through cause and effect.
- For videos over 10 minutes, include meaningful chapter-to-chapter progression, but keep markdown headings out of the spoken narration.
- For videos over 20 minutes, include objections, limitations, exceptions, or alternative explanations when grounded in the research.
- For videos over 30 minutes, organize the reasoning into acts internally, while keeping the final narration natural and continuous.
- Prefer everyday words over industry terminology.
- Use a technical term only when materially useful; explain it immediately.
- Most sentences should be short enough to visualize as one beat.
- Vary sentence length naturally. Use occasional direct questions, but do not ask a question in every paragraph.
- Use smooth spoken transitions; do not sound like bullet points being read aloud.
- Avoid sounding like a news article, academic abstract, or corporate report.
- No citations spoken aloud and no markdown headings inside narration.
- Size the conclusion according to the duration-specific strategy; do not rush a long-form synthesis or overextend a short ending.
- End with a useful takeaway, not a generic like/subscribe/share call to action.
- Keep the CTA out of narration. Write it only in the separate outro object.
- Keep the outro spoken_text close to one of these short natural lines, selecting the tone that fits the topic: "If this video helped, leave a like and subscribe for more." / "If this helped you see the pattern, like and subscribe for more." / "If this breakdown was useful, subscribe for more simple explainers."
- Stay close to {target_words} words (within about 10%) so the finished narration matches the requested duration.
- Use only facts grounded in the research JSON.
{routine_scenarios}

Return ONLY JSON:
{{
  "title": "...",
  "hook": "...",
  "opening_arc": {{
    "mirror_moments": ["exact or near-exact opening behavior moments used in narration"],
    "pattern_interrupt": "the line that reframes those moments",
    "payoff_promise": "what the viewer will understand/get by staying"
  }},
  "narration": "...",
  "takeaway": "...",
  "outro": {{
    "cta_angle": "brief benefit of future videos, matched to this topic",
    "spoken_text": "one short friendly sentence, about 10-18 words, inviting a like and/or subscription",
    "subtitle_text": "short CTA subtitle",
    "visual_style": "creator_desk_mic|monitor_play_button|whiteboard_presenter|cozy_creator_room",
    "duration_sec": 5
  }}
}}
""".strip()
        response = self.client.responses.create(
            model=TEXT_MODEL,
            input=prompt,
            max_output_tokens=max_output_tokens,
        )
        script = extract_json(response.output_text)
        script["outro"] = normalize_outro(script.get("outro"), topic, script.get("takeaway", ""))
        return script

    def generate_outro_brief(self, topic: str, script: dict,
                             preferred_style: str | None = None, fixed: bool = False) -> dict:
        """Reuse the script's CTA; ask the model only for older scripts lacking one."""
        raw = script.get("outro")
        if not isinstance(raw, dict) or not raw.get("spoken_text"):
            prompt = ("Write one short, warm English YouTube outro CTA based on this video's topic and takeaway. "
                      "Use wording close to: 'If this video helped, leave a like and subscribe for more.' "
                      "or 'If this helped you see the pattern, like and subscribe for more.' "
                      "or 'If this breakdown was useful, subscribe for more simple explainers.' "
                      "Return ONLY JSON with cta_angle, spoken_text (10-18 words, one sentence), "
                      "subtitle_text, visual_style, and duration_sec (4-8). Do not repeat the takeaway "
                      "or add factual claims. Topic: " + topic + "\nTakeaway: " + str(script.get("takeaway", "")))
            response = self.client.responses.create(model=TEXT_MODEL, input=prompt)
            raw = extract_json(response.output_text)
        return normalize_outro(raw, topic, script.get("takeaway", ""), preferred_style, fixed)

    def plan_outro_scene(self, outro_brief: dict) -> dict:
        return build_outro_scene(outro_brief)

    def tts_outro(self, outro_text: str, output_path: Path, voice: str | None = None) -> None:
        self.tts(outro_text, output_path, voice=voice)

    def generate_outro_image(self, visual_prompt: str, output_path: Path,
                             quality: str | None = None) -> None:
        self.generate_full_scene(visual_prompt, output_path, quality=quality)

    def story_blueprint(self, topic: str, research: dict, audience_brief: dict, script: dict,
                        duration_minutes: int) -> dict:
        duration_strategy = self._duration_strategy(max(1, int(duration_minutes)))
        prompt = f"""
You are the VISUAL STORY DIRECTOR, not an illustrator.
Topic: {topic}
Duration: {duration_minutes} minute(s)

Research:
{json.dumps(research, ensure_ascii=False)}

Audience brief:
{json.dumps(audience_brief, ensure_ascii=False)}

Script:
{json.dumps(script, ensure_ascii=False)}

Story-directing principles:
{STORY_RULES}

Duration-specific editorial strategy:
{duration_strategy}

Design a visual grammar for this ONE video. The visuals should tell the same story even with the sound muted.
The OPENING should visually mirror the viewer's real life before it explains the topic whenever the script contains viewer-mirror moments. Treat those moments as lived micro-scenes, not generic icons. Example pattern: red light -> hand reaches for phone; meal -> video already playing; quiet pause -> notification check.
The opening visual sequence should create recognition first, then reveal the hidden pattern, then transition into explanation. Avoid starting with an abstract diagram if the script opens with a human behavior.
Do not invent facts. Do not propose fancy decoration just to look different.
Scale the number and depth of visual beats to the duration strategy. Short videos need a tight single arc; long videos need chapters, callbacks, evolving motifs, and visual resets between major sections.

Use these scene archetypes when appropriate:
- question_reveal: viewer sees a mystery/problem before the explanation
- cause_effect: A visibly leads to B
- comparison: two states/options shown side by side
- process: a short sequence of steps
- zoom_detail: isolate one important object/detail
- consequence: show what changes for the viewer
- myth_fact: contrast an intuitive belief with the grounded explanation
- example: make an abstract idea concrete
- object_only: let objects/data carry the scene, no character
- takeaway: end on one memorable practical idea

Return ONLY JSON:
{{
  "story_promise": "what the viewer will understand by the end",
  "opening_tension": "what feels unresolved at the start",
  "viewer_mirror_sequence": [
    {{"behavior":"recognizable micro-behavior from the opening","visual_scene":"how to show it as a lived moment","transition":"how it leads to the next beat"}}
  ],
  "visual_motif": "one recurring visual motif that can connect the video without dominating it",
  "continuity_anchors": ["2-4 objects/visual ideas that may reappear intentionally"],
  "avoid_repetition": ["specific compositions/moves to avoid overusing"],
  "character_usage": "how the character acts as guide/reaction, not wallpaper",
  "arc": [
    {{"beat": 1, "purpose": "hook|context|cause|reveal|consequence|takeaway", "viewer_feeling": "curious|surprised|clear|concerned|confident", "visual_archetype": "question_reveal|cause_effect|comparison|process|zoom_detail|consequence|myth_fact|example|object_only|takeaway"}}
  ]
}}
""".strip()
        response = self.client.responses.create(model=TEXT_MODEL, input=prompt)
        return extract_json(response.output_text)

    def plan_scenes(self, script: dict, story_blueprint: dict,
                    preferred_scene_seconds: int, max_scenes: int) -> list[dict]:
        prompt = f"""
Turn the narration into a shot-by-shot VISUAL STORYBOARD for a minimalist 2D explainer.
Preferred scene length: about {preferred_scene_seconds} seconds.
Hard maximum scene count: {max_scenes}.

Narration:
{script['narration']}

Visual story blueprint:
{json.dumps(story_blueprint, ensure_ascii=False)}

Important: choose the correct scene mode. The character can be a composited GUIDE/ACTOR for simple host beats, but lived behavioral moments should be planned as integrated experiential scenes where the character physically performs the action in the environment. Do not force every scene into a standing-host PNG composition.
For background-only/host scenes, backgrounds must contain NO people. For experiential full-scene beats, the separate full-scene generator will integrate the same character identity into the environment.

For every scene:
1) preserve narration wording/order exactly;
2) assign a STORY PURPOSE: why this scene exists;
3) choose one visual archetype;
4) choose one clear focal object/relationship;
5) decide whether the character is needed. Use object-only scenes regularly (roughly 20-35% when appropriate);
6) if character is visible, give it a motivated action/reaction tied to the focal idea;
7) vary composition. Do not repeat the same character position + camera + archetype in adjacent scenes;
8) use visual continuity only when it helps the viewer track cause/effect;
9) no floating labels, top-center pills, decorative rings or filler marks. Leave on_screen_emphasis empty;
10) no decorative clutter, no unsupported charts or numbers.
11) state the semantic subject, core claim, and visual message before listing objects;
12) choose objects that prove the claim visually, not objects matched from isolated words;
13) never use calendar/checklist as generic fallback; use them only for actual schedules/tasks.
14) OPENING RECOGNITION RULE: when narration describes a familiar behavior, visualize the behavior itself as an experiential micro-scene before using diagrams. Example: "waiting at a red light and checking the phone" should show the character at a crosswalk/traffic-light context reaching for the phone, not a phone icon + clock.
15) Prefer action verbs and object interaction in behavior-led scenes: reaching, scrolling, eating while watching, glancing, opening, tapping, carrying, sitting, waiting, avoiding, checking, putting away.
16) For the first 10-25 seconds, prioritize viewer recognition and scene-to-scene progression when the script supports it. Do not immediately summarize with abstract cards if a more relatable lived scene exists.
17) Avoid repeating generic presenter poses during the recognition opening. The viewer should watch a tiny story unfold.

Allowed:
- emotion: curious|surprised|thinking|concerned|explaining|confident|neutral
- gesture: question|react|think|point|present|warning|compare|observe|none
- character_action: enter|lean_in|step_back|point_at_focus|compare_sides|inspect|present|react|think|celebrate|warn|none
- overlay_symbols: optional list of {{"type":"question_mark|exclamation_mark|check_mark|warning_mark|short_arrow|small_highlight|underline_emphasis|spark", "target":"character|focus_object"}}; use [] when no symbol is needed, at most two
- character_position: left|center|right
- focus_side: left|center|right|full
- camera: zoom_in|zoom_out|pan_left|pan_right|static
- transition: cut|match_cut|push|reveal
- visual_archetype: question_reveal|cause_effect|comparison|process|zoom_detail|consequence|myth_fact|example|object_only|takeaway

Return ONLY a JSON array:
[
  {{
    "scene_id": 1,
    "narration": "exact source narration chunk",
    "subtitle_hint": "short readable cue",
    "story_purpose": "make the viewer wonder why X happens",
    "viewer_feeling": "curious",
    "visual_archetype": "question_reveal",
    "visual_prompt": "background-only description with large simple objects and explicit composition",
    "semantic_subject": "the meaning of this scene",
    "core_claim": "the factual or experiential claim being shown",
    "visual_message": "what the viewer should understand from the image",
    "visual_concept": "habit_loop|no_magic_reset|behavior_change|notification_trigger|focus|other specific concept",
    "visual_objects": [{{"type":"phone"}},{{"type":"notification"}}],
    "visual_relationship": "sequence|comparison|negates|replacement|group",
    "focus_object": "RAM price tag",
    "focus_side": "right",
    "continuity_anchor": "RAM stick",
    "character_visible": true,
    "character_role": "reactor|guide|demonstrator|none",
    "emotion": "surprised",
    "gesture": "question",
    "character_action": "lean_in",
    "interaction_target": "RAM price tag",
    "character_position": "left",
    "character_scale": 0.48,
    "overlay_symbols": [{{"type":"question_mark","target":"character"}}],
    "on_screen_emphasis": "",
    "camera": "zoom_in",
    "transition": "cut"
  }}
]
""".strip()
        response = self.client.responses.create(model=TEXT_MODEL, input=prompt)
        scenes = extract_json(response.output_text)
        if not isinstance(scenes, list):
            raise RuntimeError("Scene planner khÃ´ng tráº£ vá» má»™t máº£ng JSON.")
        return scenes[:max_scenes]

    def generate_background(self, scene_prompt: str, output_path: Path,
                            quality: str | None = None, size: str = "1536x1024") -> None:
        full_prompt = f"""
{VISUAL_STYLE}

Scene content and composition:
{scene_prompt}

Composition requirements:
- 16:9 landscape composition.
- One instantly readable focal idea.
- Show relationships spatially (before/after, A -> B, comparison, sequence) when requested.
- Leave intentional negative space for a separate cartoon character only if the scene description implies one.
- No people, no human silhouettes, no text, no watermark.
- Do not decorate empty areas with irrelevant objects.
- No decorative rings, floating labels, top-center text, UI pill badges, or random callouts.
""".strip()
        self.image_provider.generate_image(full_prompt,output_path,model=IMAGE_MODEL,
                                           quality=quality or IMAGE_QUALITY,size=size)

    def generate_full_scene(self, scene_prompt: str, output_path: Path,
                            quality: str | None = None, size: str = "1536x1024") -> None:
        scene_style=(VISUAL_STYLE.replace("no people, no human silhouettes,", "")
                     .replace("simple geometric objects, sparse composition", "meaningful environmental detail")
                     .replace("Use a clean minimal composition", "Use a clean story composition"))
        prompt=(f"{scene_style}\nCreate a complete scene matching this spoken idea: {scene_prompt}\n"
                "Use the supplied character reference for the SAME character identity and clothing. "
                "Integrate that character naturally into the action. One character only. "
                "No unrelated decorations, captions, logos, or watermark.")
        self.image_provider.edit_image(prompt,CHARACTER_PATH,output_path,model=IMAGE_MODEL,
                                       quality=quality or IMAGE_QUALITY,size=size)

    def tts(self, text: str, output_path: Path, voice: str | None = None) -> None:
        voice = voice or TTS_VOICE
        with self.client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=voice,
            input=text,
            instructions=(
                "Natural English YouTube explainer narration. Warm, conversational and curious. "
                "Use small pauses around reveals, contrasts and questions. Clear pronunciation, medium pace."
            ),
            response_format="wav",
        ) as response:
            response.stream_to_file(output_path)

