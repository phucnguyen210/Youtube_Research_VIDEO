from __future__ import annotations
import math
import wave
import hashlib
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .config import VIDEO_W, VIDEO_H
from .outro import normalize_outro, plan_outro_scene as build_outro_scene, render_local_outro


class MockService:
    """Offline/demo service showing the V3 visual-storytelling architecture."""

    def research(self, topic, sources):
        return {
            "topic": topic,
            "one_sentence_answer": "Demo research exists to test the V3 visual-story pipeline without API calls.",
            "key_points": [
                {"point": "One priority reduces decision overload.", "why_it_matters": "The viewer can act immediately.", "plain_english": "Pick the one thing that matters most first.", "visualizable_as": ["comparison", "example"], "confidence": "medium", "source_urls": []},
                {"point": "Distractions compete for attention.", "why_it_matters": "Environment design can make focus easier.", "plain_english": "Make distractions harder to reach.", "visualizable_as": ["cause_effect", "before_after"], "confidence": "medium", "source_urls": []},
                {"point": "Repeatable routines beat complicated plans.", "why_it_matters": "Consistency is easier to maintain.", "plain_english": "Simple enough to repeat beats perfect once.", "visualizable_as": ["comparison", "process"], "confidence": "medium", "source_urls": []},
            ],
            "jargon_to_translate": [],
            "sources": [{"title": "Demo mode", "url": "", "platform": "demo", "why_useful": "Pipeline test only"}],
        }

    def audience_brief(self, topic, research, audience, retention_level):
        return {
            "viewer_question": f"What is the simplest useful answer to {topic}?",
            "hook_options": ["Most routines fail for a surprisingly simple reason.", "The perfect routine is probably simpler than you think.", "If your routine keeps falling apart, start here."],
            "core_payoff": "Reduce friction and make the useful choice easier to repeat.",
            "simple_explanations": ["Pick one priority.", "Move distractions away.", "Keep the routine repeatable."],
            "avoid_or_translate": [],
            "curiosity_beats": ["question", "small reveal", "cause", "consequence", "takeaway"],
            "recommended_structure": ["hook", "context", "cause", "why_it_matters", "takeaway"],
        }

    def write_script(self, topic, research, audience_brief, duration_minutes, audience, retention_level):
        base = (
            "The perfect routine is probably simpler than you think. "
            "Most people keep adding habits, but the real problem is often friction. "
            "Start with one important task and make that task the easiest thing to begin. "
            "Move your phone away before you sit down. "
            "Then use one short focus block instead of planning hours of perfect concentration. "
            "The goal is not an impressive schedule. It is a routine you can repeat tomorrow."
        )
        if "ram" in topic.lower() or "dram" in topic.lower():
            base = (
                "Why is RAM getting more expensive? "
                "AI servers need enormous pools of memory, while ordinary computers need it too. "
                "Manufacturers shift limited factory capacity toward server memory. "
                "That leaves fewer chips for ordinary buyers. "
                "A smaller consumer supply can put pressure on prices. "
                "Compare what you need now with current options before buying."
            )
        target_words = duration_minutes * 145
        sentences = [s.strip() for s in re.findall(r"[^.!?]+[.!?]",base) if s.strip()]
        repeated = sentences * max(2, math.ceil(target_words / max(1, len(base.split())))+1)
        best = min(range(1,len(repeated)+1),key=lambda n:abs(sum(len(s.split()) for s in repeated[:n])-target_words))
        chosen = repeated[:best]
        if chosen[-1] != sentences[-1]:
            chosen.append(sentences[-1])
        narration = " ".join(chosen)
        takeaway = "Make the useful choice easier to repeat."
        outro = normalize_outro({"subtitle_text": "Like and subscribe for more"}, topic, takeaway)
        return {"title": topic, "hook": "The perfect routine is probably simpler than you think.",
                "narration": narration, "takeaway": takeaway, "outro": outro}

    def generate_outro_brief(self, topic, script, preferred_style=None, fixed=False):
        return normalize_outro(script.get("outro"), topic, script.get("takeaway", ""), preferred_style, fixed)

    def plan_outro_scene(self, outro_brief):
        return build_outro_scene(outro_brief)

    def tts_outro(self, outro_text, output_path, voice=None):
        self.tts(outro_text, output_path, voice=voice)

    def generate_outro_image(self, visual_prompt, output_path, quality=None):
        render_local_outro(normalize_outro({}, "demo"), output_path)

    def story_blueprint(self, topic, research, audience_brief, script, duration_minutes):
        return {
            "story_promise": "Show why simpler routines are easier to repeat.",
            "opening_tension": "Why do complicated routines collapse even when motivation is high?",
            "visual_motif": "a single path that becomes clearer as distractions are removed",
            "continuity_anchors": ["phone", "desk", "one task card"],
            "avoid_repetition": ["character standing left every scene", "zoom-in every scene", "same room composition"],
            "character_usage": "Character reacts to problems, demonstrates choices, then disappears for object-only explanation beats.",
            "arc": [
                {"beat": 1, "purpose": "hook", "viewer_feeling": "curious", "visual_archetype": "question_reveal"},
                {"beat": 2, "purpose": "reveal", "viewer_feeling": "surprised", "visual_archetype": "comparison"},
                {"beat": 3, "purpose": "cause", "viewer_feeling": "clear", "visual_archetype": "cause_effect"},
                {"beat": 4, "purpose": "consequence", "viewer_feeling": "clear", "visual_archetype": "object_only"},
                {"beat": 5, "purpose": "takeaway", "viewer_feeling": "confident", "visual_archetype": "takeaway"},
            ],
        }

    def plan_scenes(self, script, story_blueprint, preferred_scene_seconds, max_scenes):
        sentences = [s.strip() for s in script["narration"].replace("!", ".").replace("?", ".").split(".") if s.strip()]
        presets = [
            dict(purpose="hook", feeling="curious", archetype="question_reveal", emotion="curious", gesture="question", action="lean_in", symbols=["question_mark"], pos="left", focus="right", camera="zoom_in", role="reactor", visible=True, emphasis="Why?"),
            dict(purpose="reveal", feeling="surprised", archetype="comparison", emotion="surprised", gesture="compare", action="compare_sides", symbols=["exclamation_mark"], pos="center", focus="full", camera="zoom_out", role="demonstrator", visible=True, emphasis=""),
            dict(purpose="cause", feeling="clear", archetype="cause_effect", emotion="explaining", gesture="point", action="point_at_focus", symbols=["arrow"], pos="left", focus="right", camera="pan_right", role="guide", visible=True, emphasis="Reduce friction"),
            dict(purpose="example", feeling="clear", archetype="object_only", emotion="neutral", gesture="none", action="none", symbols=[], pos="right", focus="center", camera="static", role="none", visible=False, emphasis=""),
            dict(purpose="consequence", feeling="clear", archetype="process", emotion="thinking", gesture="observe", action="inspect", symbols=["arrow"], pos="right", focus="left", camera="pan_left", role="guide", visible=True, emphasis="Start small"),
            dict(purpose="takeaway", feeling="confident", archetype="takeaway", emotion="confident", gesture="present", action="present", symbols=[{"type":"check_mark","target":"focus_object"}], pos="left", focus="center", camera="zoom_in", role="guide", visible=True, emphasis=""),
        ]
        if "RAM" in script["narration"]:
            presets = [
                dict(purpose="hook", feeling="curious", archetype="question_reveal", emotion="surprised", gesture="question", action="react", symbols=["question_mark"], pos="left", focus="right", camera="push_in", role="reactor", visible=True, emphasis="Why now?"),
                dict(purpose="demand", feeling="surprised", archetype="object_only", emotion="neutral", gesture="none", action="none", symbols=[], pos="left", focus="center", camera="static", role="none", visible=False, emphasis="Server demand"),
                dict(purpose="cause", feeling="clear", archetype="cause_effect", emotion="neutral", gesture="none", action="none", symbols=[], pos="right", focus="center", camera="pan_right", role="none", visible=False, emphasis="Factory shift"),
                dict(purpose="consequence", feeling="concerned", archetype="consequence", emotion="concerned", gesture="warning", action="warn", symbols=["warning_mark"], pos="right", focus="left", camera="push_in", role="reactor", visible=True, emphasis=""),
                dict(purpose="price", feeling="concerned", archetype="consequence", emotion="concerned", gesture="warning", action="warn", symbols=[], pos="left", focus="right", camera="push_in", role="guide", visible=True, emphasis="Price pressure"),
                dict(purpose="takeaway", feeling="confident", archetype="takeaway", emotion="confident", gesture="present", action="present", symbols=[{"type":"check_mark","target":"focus_object"}], pos="left", focus="center", camera="pull_out", role="guide", visible=True, emphasis=""),
            ]
        if len(sentences) > max_scenes:
            groups=[sentences[i*len(sentences)//max_scenes:(i+1)*len(sentences)//max_scenes]
                    for i in range(max_scenes)]
        else:
            groups=[[sentence] for sentence in sentences]
        scenes=[]
        for idx, group in enumerate(groups,1):
            sentence=". ".join(group)
            pr=presets[(idx-1)%len(presets)]
            scenes.append({
                "scene_id": idx, "narration": sentence+".", "subtitle_hint": " ".join(sentence.split()[:8]),
                "story_purpose": pr["purpose"], "viewer_feeling": pr["feeling"], "visual_archetype": pr["archetype"],
                "visual_prompt": f"Minimal 2D explainer scene for '{sentence[:150]}'. Focal idea on the {pr['focus']}. Use a different composition from adjacent scenes.",
                "focus_object": "one clear object or relationship", "focus_side": pr["focus"], "continuity_anchor": "phone/desk/task card",
                "character_visible": pr["visible"], "character_role": pr["role"], "emotion": pr["emotion"], "gesture": pr["gesture"],
                "character_action": pr["action"], "interaction_target": "focal object", "character_position": pr["pos"], "character_scale": 0.46,
                "overlay_symbols": pr["symbols"], "on_screen_emphasis": "", "camera": pr["camera"], "transition": "cut",
            })
        return scenes

    def generate_background(self, scene_prompt: str, output_path: Path):
        im = Image.new("RGB", (VIDEO_W, VIDEO_H), (250, 249, 245))
        d = ImageDraw.Draw(im)
        ink=(48,53,61); yellow=(244,194,73); pale=(255,239,192)
        d.line((0, 860, VIDEO_W, 860), fill=ink, width=4)
        low=scene_prompt.lower()
        if "ram" in low or "memory" in low or "chip" in low:
            def module(x,y,w=230,h=110):
                d.rounded_rectangle((x,y,x+w,y+h),radius=12,fill=(255,255,255),outline=ink,width=8)
                for k in range(4):
                    d.rectangle((x+28+k*45,y+25,x+58+k*45,y+75),fill=pale,outline=ink,width=3)
                for k in range(6):
                    d.line((x+25+k*36,y+h,x+25+k*36,y+h+22),fill=yellow,width=8)
            def rack(x,y):
                d.rounded_rectangle((x,y,x+235,y+420),radius=16,fill=(234,238,238),outline=ink,width=8)
                for k in range(4):
                    d.rounded_rectangle((x+20,y+25+k*95,x+215,y+90+k*95),radius=8,fill=(255,255,255),outline=ink,width=4)
                    d.rectangle((x+180,y+48+k*95,x+195,y+63+k*95),fill=yellow)
            def arrow(x1,y1,x2,y2):
                d.line((x1,y1,x2,y2),fill=yellow,width=16)
                d.polygon([(x2,y2),(x2-40,y2-25),(x2-40,y2+25)],fill=yellow)
            if "factory" in low or "manufactur" in low:
                d.polygon([(570,650),(570,360),(770,450),(770,360),(970,450),(970,650)],fill=(235,238,238),outline=ink)
                d.rectangle((580,650,970,680),fill=ink)
                arrow(1000,500,1230,390); arrow(1000,540,1230,680)
                rack(1270,210); module(1280,650,190,85)
            elif "fewer" in low or "less supply" in low:
                module(650,380); module(1050,380)
                d.line((1330,340,1330,620),fill=ink,width=8)
                d.line((1350,340,1350,620),fill=ink,width=8)
            elif "price" in low or "expensive" in low:
                module(720,420,340,145)
                d.rounded_rectangle((1220,350,1500,590),radius=24,fill=pale,outline=ink,width=8)
                d.line((1360,510,1360,405),fill=yellow,width=18)
                d.polygon([(1360,385),(1325,440),(1395,440)],fill=yellow)
            elif "server" in low:
                module(600,400); rack(1240,260)
                arrow(870,460,1200,460)
            else:
                module(830,420,350,150)
            im.save(output_path,quality=92)
            return
        key=int.from_bytes(hashlib.sha256(scene_prompt.encode()).digest()[:2],"big")
        arch_match=re.search(r"Visual archetype:\s*([\w_]+)",scene_prompt)
        arch=arch_match.group(1) if arch_match else "example"
        focus_match=re.search(r"Primary focus:\s*(.+?)\.",scene_prompt)
        label=(focus_match.group(1) if focus_match else scene_prompt)[:52]
        focus_side="right" if "on the right" in scene_prompt else "left" if "on the left" in scene_prompt else "center"
        centers={"left":[590,1050],"center":[750,1230],"right":[850,1370]}[focus_side]
        for n,cx in enumerate(centers):
            cy=450+(key%4-2)*25 if n==0 else 450-(key%3-1)*35
            fill=(255,255,255) if n==0 else pale
            if arch in {"process","cause_effect"}:
                d.rounded_rectangle((cx-170,cy-110,cx+170,cy+110),radius=55,fill=fill,outline=ink,width=8)
            else:
                d.rounded_rectangle((cx-165,cy-155,cx+165,cy+155),radius=28,fill=fill,outline=ink,width=8)
        d.line((centers[0]+180,450,centers[1]-180,450),fill=yellow,width=17)
        d.polygon([(centers[1]-180,450),(centers[1]-225,420),(centers[1]-225,480)],fill=yellow)
        im.save(output_path, quality=92)

    def tts(self, text: str, output_path: Path, voice=None):
        duration = max(1.5, len(text.split()) / 145 * 60)
        rate = 24000
        frames = int(duration * rate)
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate); wf.writeframes(b"\x00\x00" * frames)
