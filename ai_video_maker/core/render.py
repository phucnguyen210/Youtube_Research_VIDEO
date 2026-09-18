from __future__ import annotations
import re
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import imageio_ffmpeg

from .config import CHARACTER_PATH, ASSETS_DIR, VIDEO_W, VIDEO_H
from .character_pose_selector import select_pose
from .overlays import normalize_overlays


def cover_crop(im: Image.Image, size=(VIDEO_W, VIDEO_H)) -> Image.Image:
    tw, th = size
    ratio = max(tw / im.width, th / im.height)
    nw, nh = round(im.width * ratio), round(im.height * ratio)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return im.crop((left, top, left + tw, top + th))


def _font(size: int):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def _character_transform(char: Image.Image, emotion: str, gesture: str) -> Image.Image:
    # V3 fallback acting: preserve the original character artwork, but vary body language
    # through subtle tilt/flip/scale. Custom pose PNGs can later override this without
    # changing the rest of the pipeline.
    tilt = {
        "curious": -3,
        "surprised": 2,
        "thinking": -4,
        "concerned": 3,
        "explaining": 0,
        "confident": -1,
        "neutral": 0,
    }.get(emotion, 0)
    if gesture == "point":
        char = ImageOps.mirror(char)
    if emotion == "surprised":
        char = char.resize((int(char.width * 1.04), int(char.height * 1.04)), Image.Resampling.LANCZOS)
    if tilt:
        char = char.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
    return char


def _draw_symbol(draw: ImageDraw.ImageDraw, symbol: str, x: int, y: int, scale: float = 1.0):
    ink = (43, 49, 55, 255)
    yellow = (244, 190, 56, 255)
    if symbol in {"question_mark", "exclamation_mark"}:
        glyph = {"question_mark":"?", "exclamation_mark":"!"}[symbol]
        draw.text((x,y),glyph,font=_font(int(72*scale)),fill=yellow,
                  stroke_width=max(1,int(2*scale)),stroke_fill=ink)
    elif symbol == "check_mark":
        draw.line([(x-int(24*scale),y),(x-int(5*scale),y+int(19*scale)),
                   (x+int(34*scale),y-int(27*scale))],fill=yellow,width=max(4,int(9*scale)),joint="curve")
    elif symbol == "warning_mark":
        rr=int(36*scale)
        draw.polygon([(x,y-rr),(x-rr,y+rr),(x+rr,y+rr)],fill=(255,223,120,255),outline=ink)
        draw.text((x-int(10*scale),y-int(24*scale)),"!",font=_font(int(45*scale)),fill=ink)
    elif symbol == "short_arrow":
        end=x+int(75*scale)
        draw.line((x,y,end,y),fill=yellow,width=max(3,int(7*scale)))
        draw.polygon([(end,y),(end-int(18*scale),y-int(13*scale)),(end-int(18*scale),y+int(13*scale))],fill=yellow)
    elif symbol == "small_highlight":
        draw.rounded_rectangle((x-int(48*scale),y-int(38*scale),x+int(48*scale),y+int(38*scale)),
                               radius=int(12*scale),outline=yellow,width=max(2,int(5*scale)))
    elif symbol == "underline_emphasis":
        draw.line((x-int(45*scale),y,x+int(45*scale),y),fill=yellow,width=max(3,int(7*scale)))
    elif symbol == "spark":
        rr=int(24*scale)
        draw.line((x-rr,y,x+rr,y),fill=yellow,width=max(2,int(5*scale)))
        draw.line((x,y-rr,x,y+rr),fill=yellow,width=max(2,int(5*scale)))


def composite_scene(background_path: Path, output_path: Path, character_visible: bool,
                    position: str, scale: float, emotion: str = "neutral",
                    gesture: str = "none", overlay_symbols: list[str] | None = None,
                    character_action: str = "none", focus_side: str = "center",
                    interaction_target: str = "", on_screen_emphasis: str = "",
                    visual_archetype: str = "example", character_pose: str | None = None):
    bg = cover_crop(Image.open(background_path).convert("RGBA"))
    overlay_symbols = normalize_overlays(overlay_symbols or [],visual_archetype,character_visible)

    if character_visible:
        source_path, has_pose = select_pose(emotion, character_action, visual_archetype, character_pose)
        char = Image.open(source_path).convert("RGBA")
        scale = max(0.15, min(float(scale), 0.35))
        target_h = int(VIDEO_H * scale)
        target_w = int(char.width * target_h / char.height)
        char = char.resize((target_w, target_h), Image.Resampling.LANCZOS)
        if not has_pose:
            char = _character_transform(char, emotion, gesture)
        # V3 action acting: preserve the source art, but change body language and stage position.
        if character_action in {"lean_in", "inspect", "point_at_focus"}:
            char = char.rotate(-3 if position != "right" else 3, resample=Image.Resampling.BICUBIC, expand=True)
        if character_action in {"react", "step_back"}:
            nw=max(1,int(char.width*.95)); nh=max(1,int(char.height*.95)); char=char.resize((nw,nh),Image.Resampling.LANCZOS)
        if character_action in {"present", "celebrate"}:
            nw=max(1,int(char.width*1.03)); nh=max(1,int(char.height*1.03)); char=char.resize((nw,nh),Image.Resampling.LANCZOS)
        y = VIDEO_H - char.height - 38
        if character_action in {"enter", "present", "celebrate"}: y -= 18
        if emotion == "surprised":
            y -= 16
        if position == "left":
            x = 105
        elif position == "right":
            x = VIDEO_W - char.width - 105
        else:
            x = (VIDEO_W - char.width) // 2
        bg.alpha_composite(char, (x, y))
    draw = ImageDraw.Draw(bg)
    for item in overlay_symbols:
        if item["target"] == "character" and character_visible:
            sx = x-35 if position == "right" else x+char.width+8
            sy = y+35
        else:
            sx = {"left":420,"center":960,"right":1500,"full":960}.get(focus_side,960)
            sy = 520
            if item["type"] == "check_mark": sx += 105
        _draw_symbol(draw,item["type"],int(sx),int(sy),0.8)
    bg.convert("RGB").save(output_path, quality=94)


def camera_filter(camera: str, duration: float, fps: int, strength: float = 0.05, focus_side: str = "center") -> str:
    frames = max(1, int(round(duration * fps)))
    strength = max(0.0, min(0.07, float(strength)))
    progress = f"min(1,max(0,on/{max(1,frames-1)}))"
    ease = f"({progress})*({progress})*(3-2*({progress}))"
    if camera == "static":
        z = "1.0"
    elif camera in {"zoom_out", "pull_out"}:
        z = f"1+{strength:.4f}*(1-({ease}))"
    elif camera in {"pan_left", "pan_right"}:
        z = f"1+{max(.025,strength):.4f}"
    else:
        z = f"1+{strength:.4f}*({ease})"
    focus = {"left": .38, "right": .62}.get(focus_side, .5)
    if camera == "pan_left":
        fraction = f"1-({ease})"
    elif camera == "pan_right":
        fraction = ease
    else:
        fraction = f"{focus:.2f}"
    x = f"(iw-iw/zoom)*({fraction})"
    y = "(ih-ih/zoom)/2"
    return f"scale=2304:1296,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={VIDEO_W}x{VIDEO_H}:fps={fps},format=yuv420p"


def render_scene(image_path: Path | list[Path], audio_path: Path, out_path: Path, duration: float, fps: int, camera: str, beats: list[dict] | None = None):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    images = image_path if isinstance(image_path, list) else [image_path]
    beats = beats or [{"duration":duration,"camera":camera,"focus_side":"center","camera_strength":0.05}]
    cmd = [ffmpeg, "-y"]
    for image in images:
        cmd += ["-loop", "1", "-framerate", str(fps), "-t", f"{1/fps:.6f}", "-i", str(image)]
    cmd += ["-i", str(audio_path)]
    filters = []
    for i, beat in enumerate(beats):
        vf = camera_filter(beat.get("camera",camera),float(beat["duration"]),fps,
                           beat.get("camera_strength",0.05),beat.get("focus_side","center"))
        filters.append(f"[{i}:v]{vf},setpts=PTS-STARTPTS[v{i}]")
    filters.append("".join(f"[v{i}]" for i in range(len(images)))+f"concat=n={len(images)}:v=1:a=0[v]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", f"{len(images)}:a",
            "-t", f"{duration:.3f}", "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-shortest", str(out_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def concat_scenes(clips: list[Path], out_path: Path, fps: int = 30):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    concat_file = out_path.parent / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in clips), encoding="utf-8")
    cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
           "-vf", f"fps={fps}", "-r", str(fps), "-fps_mode", "cfr",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", str(out_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def srt_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _split_for_subtitles(text: str, max_words: int = 8) -> list[str]:
    # Prefer sentence/clause boundaries, then split long chunks at word boundaries.
    chunks=[]
    for sentence in _sentences(text):
        clauses = re.split(r"(?<=[,;:])\s+", sentence)
        for clause in clauses:
            words=clause.split()
            while len(words) > max_words:
                # Keep chunks roughly 5-8 words instead of tiny fragments.
                take=min(max_words, max(5, len(words)//2))
                chunks.append(" ".join(words[:take]))
                words=words[take:]
            if words:
                chunks.append(" ".join(words))
    return chunks or [text.strip()]


def _wrap_subtitle(text: str, width: int = 34) -> str:
    lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) <= 2:
        return "\n".join(lines)
    # For safety, rebalance into at most two lines.
    words=text.split(); half=(len(words)+1)//2
    return " ".join(words[:half]) + "\n" + " ".join(words[half:])


def write_srt(scenes: list[dict], path: Path):
    """Create short, readable subtitle cards timed proportionally to spoken words."""
    t = 0.0
    blocks=[]
    idx=1
    for scene in scenes:
        dur = float(scene.get("duration", 0) or 0)
        if dur <= 0 or dur > 600:
            raise RuntimeError(f"Scene duration bất thường: {dur}")
        text = scene.get("narration", "").strip()
        chunks = _split_for_subtitles(text, max_words=8)
        weights = [max(1, len(re.findall(r"\w+", c))) for c in chunks]
        total = sum(weights)
        local = 0.0
        for c, w in zip(chunks, weights):
            piece = dur * w / total
            start = t + local
            end = min(t + dur, start + piece)
            # Avoid unreadably tiny subtitle cards; neighboring proportional timing is
            # still preserved overall for normal narration lengths.
            if end - start < 0.65:
                end = min(t + dur, start + 0.65)
            blocks.append(f"{idx}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{_wrap_subtitle(c)}\n")
            idx += 1
            local += piece
        t += dur
    path.write_text("\n".join(blocks), encoding="utf-8")
