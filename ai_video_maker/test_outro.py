"""Offline checks for AI script schema, brief, art, voice, and clip output."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
from PIL import Image

from core.mock_service import MockService
from core.openai_service import OpenAIService
from core.outro import normalize_outro, plan_outro_scene, render_local_outro, outro_asset_path, choose_style
from core.render import render_scene
from core.utils import media_duration


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text='{"title":"Study habits","hook":"A familiar start.",'
            '"narration":"A familiar start. One useful study habit.",'
            '"takeaway":"Start with one task.","outro":{'
            '"cta_angle":"practical_ideas","spoken_text":"If this helped you study a little more clearly, '
            'leave a like and subscribe for more practical ideas.",'
            '"subtitle_text":"Like and subscribe for more","visual_style":"whiteboard_presenter",'
            '"duration_sec":5}}')


def main():
    fake = FakeResponses()
    service = object.__new__(OpenAIService)
    service.client = SimpleNamespace(responses=fake)
    script = service.write_script("Study habits", {}, {}, 1, "students", "balanced")
    assert script["narration"].startswith(script["hook"])
    assert 12 <= len(script["outro"]["spoken_text"].split()) <= 28
    assert "outro" in fake.calls[0]["input"]
    brief = service.generate_outro_brief("Study habits", script, "creator_desk_mic", fixed=True)
    assert brief["visual_style"] == "creator_desk_mic"
    assert brief["template"] == "studio_cta"
    assert len(fake.calls) == 1  # Reuse script CTA; no second text API call.
    plan = service.plan_outro_scene(brief)
    assert plan["character_visible"] and "supplied main character reference" in plan["visual_prompt"]
    assert "No written words" in plan["visual_prompt"]
    calls = []
    class FakeImageProvider:
        def edit_image(self, prompt, reference_path, output_path, **kwargs):
            calls.append((prompt, reference_path, kwargs))
            Image.new("RGB", (1536, 1024), "white").save(output_path)
    service.image_provider = FakeImageProvider()
    dynamic = normalize_outro(script["outro"], "Why is RAM expensive?", preferred_style="creator_desk_mic")
    assert dynamic["visual_style"] == "monitor_play_button"
    assert choose_style("Daily routine for students") == "whiteboard_presenter"
    root = Path("projects/outro_test")
    root.mkdir(parents=True, exist_ok=True)
    generated = root / "outro_ai_stub.png"
    service.generate_outro_image(plan["visual_prompt"], generated, quality="low")
    assert generated.is_file() and len(calls) == 1
    assert calls[0][1].name == "main.png" and calls[0][2]["quality"] == "low"
    voice_calls = []
    service.tts = lambda text, path, voice=None: voice_calls.append((text, path, voice))
    service.tts_outro(brief["spoken_text"], root / "voice_stub.wav", voice="marin")
    assert voice_calls == [(brief["spoken_text"], root / "voice_stub.wav", "marin")]
    image = root / "outro_scene.png"
    audio = root / "outro_audio.wav"
    clip = root / "outro.mp4"
    render_local_outro(brief, image)
    assert image.is_file() and image.stat().st_size > 1000
    assert hashlib.sha256(image.read_bytes()).digest() == hashlib.sha256(outro_asset_path(brief["visual_style"]).read_bytes()).digest()
    for style in ("creator_desk_mic", "monitor_play_button", "whiteboard_presenter"):
        source = outro_asset_path(style)
        assert source and source.is_file(), style
        target = root / f"check_{style}.png"
        render_local_outro({"visual_style": style}, target)
        assert target.read_bytes() == source.read_bytes()
    for topic, expected in (("Why is RAM expensive?", "If this breakdown was useful, subscribe for more simple explainers."),
                            ("Changing a habit", "If this helped you see the pattern, like and subscribe for more."),
                            ("A useful idea", "If this video helped, leave a like and subscribe for more.")):
        assert normalize_outro({}, topic)["spoken_text"] == expected
    mock = MockService()
    mock.tts_outro(brief["spoken_text"], audio, voice="marin")
    duration = media_duration(audio)
    assert 0 < duration < 20
    render_scene([image], audio, clip, duration, 24, "static")
    assert clip.is_file() and clip.stat().st_size > 1000
    print("OUTRO TEST OK", round(duration, 2))


if __name__ == "__main__":
    main()
