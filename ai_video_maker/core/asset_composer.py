"""Pillow layouts with reusable PNGs and deterministic shape fallbacks."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from .config import ASSETS_DIR

SIZE = (2048, 1152)
INK = (48, 53, 61)
YELLOW = (244, 194, 73)
PALE = (255, 239, 192)
GROUPS = {
    "alarm_clock":"routine", "calendar":"routine", "checklist":"routine", "bed":"routine",
    "desk":"routine", "phone":"routine", "water":"routine", "book":"study", "timer":"study",
    "laptop":"study", "ram":"tech", "server":"tech", "factory":"tech", "price":"ui",
    "brain":"misc", "reset_x":"ui", "timeline":"ui", "notification":"ui",
    "reward":"ui", "habit_loop":"ui", "behavior":"misc", "environment":"misc",
    "social_media":"ui", "hourglass":"ui", "attention":"ui", "focus":"ui",
    "walking":"misc", "exercise":"misc", "person":"misc", "tank":"misc",
    "friction":"ui", "urge":"ui", "notification_off":"ui", "conversation":"misc",
    "idea":"misc", "action":"misc",
    "app_screen":"ui", "lamp":"study", "mug":"study", "notebook":"study",
    "papers":"study", "chair":"routine", "dumbbell":"misc", "gym_bench":"misc",
    "progress_bar":"ui", "bag":"study", "mat":"misc", "sun":"misc", "window":"routine",
    "priority_cards":"study", "poison_bottle":"misc",
    "moon":"misc", "night_window":"routine", "mirror":"misc",
}


def _font(size: int):
    for path in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _icon(draw: ImageDraw.ImageDraw, kind: str, box: tuple[int,int,int,int]):
    x0,y0,x1,y1 = box
    cx=(x0+x1)//2; cy=(y0+y1)//2; w=x1-x0; h=y1-y0
    if kind == "poison_bottle":
        draw.rounded_rectangle((cx-68,cy-82,cx+68,cy+110),radius=14,fill="white",outline=INK,width=7)
        draw.rectangle((cx-40,cy-113,cx+40,cy-82),fill=PALE,outline=INK,width=6)
        draw.ellipse((cx-32,cy-20,cx+32,cy+44),fill=PALE,outline=INK,width=5)
        draw.line((cx-22,cy+8,cx+22,cy+8),fill=INK,width=6)
        draw.line((cx-34,cy+57,cx+34,cy+57),fill=INK,width=6)
    elif kind == "brain":
        for dx,dy in ((-58,-36),(0,-65),(62,-29),(-65,35),(10,38),(65,45)):
            draw.ellipse((cx+dx-48,cy+dy-48,cx+dx+48,cy+dy+48),fill=PALE,outline=INK,width=5)
        draw.line((cx,cy-112,cx,cy+105),fill=INK,width=5)
    elif kind == "reset_x":
        draw.arc((cx-95,cy-95,cx+95,cy+95),35,320,fill=INK,width=12)
        draw.polygon([(cx+85,cy-78),(cx+113,cy-78),(cx+99,cy-45)],fill=INK)
        draw.line((cx-90,cy-90,cx+90,cy+90),fill=(201,70,67),width=18)
        draw.line((cx+90,cy-90,cx-90,cy+90),fill=(201,70,67),width=18)
    elif kind == "timeline":
        draw.line((cx-140,cy,cx+140,cy),fill=INK,width=8)
        for dx in (-115,-35,45,125): draw.ellipse((cx+dx-11,cy-11,cx+dx+11,cy+11),fill=YELLOW,outline=INK,width=3)
        draw.text((cx+65,cy+28),"30",font=_font(48),fill=INK)
    elif kind in {"notification","notification_off"}:
        draw.rounded_rectangle((cx-120,cy-75,cx+120,cy+75),radius=20,fill="white",outline=INK,width=7)
        draw.ellipse((cx-91,cy-23,cx-43,cy+25),fill=YELLOW)
        draw.line((cx-20,cy-20,cx+88,cy-20),fill=INK,width=6)
        draw.line((cx-20,cy+22,cx+55,cy+22),fill=INK,width=5)
        if kind=="notification_off": draw.line((cx-120,cy-105,cx+120,cy+105),fill=(201,70,67),width=14)
    elif kind == "friction":
        draw.line((cx-110,cy-100,cx-110,cy+100),fill=INK,width=12)
        draw.line((cx-110,cy+100,cx+110,cy+100),fill=INK,width=12)
        draw.line((cx+110,cy+100,cx+110,cy-100),fill=INK,width=12)
        draw.line((cx-110,cy-100,cx+110,cy-100),fill=YELLOW,width=16)
    elif kind == "urge":
        draw.arc((cx-105,cy-105,cx+105,cy+105),30,320,fill=INK,width=8)
        draw.polygon([(cx+78,cy-83),(cx+115,cy-75),(cx+95,cy-40)],fill=YELLOW)
        draw.ellipse((cx-25,cy-25,cx+25,cy+25),fill=PALE,outline=INK,width=5)
    elif kind == "conversation":
        draw.ellipse((cx-120,cy-75,cx+15,cy+50),fill="white",outline=INK,width=7)
        draw.ellipse((cx-5,cy-35,cx+125,cy+85),fill=PALE,outline=INK,width=7)
        draw.line((cx-85,cy-20,cx-5,cy-20),fill=INK,width=5)
        draw.line((cx+25,cy+30,cx+90,cy+30),fill=INK,width=5)
    elif kind == "idea":
        draw.ellipse((cx-95,cy-95,cx+95,cy+65),fill=PALE,outline=INK,width=7)
        for dx,dy,r in ((-65,105,10),(-40,83,15),(-5,60,20)):
            draw.ellipse((cx+dx-r,cy+dy-r,cx+dx+r,cy+dy+r),fill=PALE,outline=INK,width=4)
    elif kind == "action":
        draw.line((cx-120,cy,cx+75,cy),fill=INK,width=14)
        draw.polygon([(cx+75,cy-65),(cx+145,cy),(cx+75,cy+65)],fill=YELLOW,outline=INK)
    elif kind in {"lamp","sun","moon"}:
        if kind=="lamp":
            draw.polygon([(cx-75,cy-35),(cx+75,cy-35),(cx+45,cy-95),(cx-45,cy-95)],fill=PALE,outline=INK)
            draw.line((cx,cy-35,cx,cy+90),fill=INK,width=8); draw.line((cx-65,cy+90,cx+65,cy+90),fill=INK,width=8)
        else:
            draw.ellipse((cx-75,cy-75,cx+75,cy+75),fill=YELLOW if kind=="sun" else PALE,outline=INK,width=6)
            if kind=="moon": draw.ellipse((cx-20,cy-105,cx+95,cy+35),fill=(250,249,245))
    elif kind == "mug":
        draw.rounded_rectangle((cx-65,cy-75,cx+65,cy+85),radius=15,fill=PALE,outline=INK,width=7)
        draw.arc((cx+40,cy-35,cx+110,cy+55),270,90,fill=INK,width=8)
    elif kind in {"notebook","papers","app_screen"}:
        draw.rounded_rectangle((cx-95,cy-105,cx+95,cy+105),radius=8,fill="white",outline=INK,width=6)
        for dy in (-60,-15,30,75): draw.line((cx-65,cy+dy,cx+65,cy+dy),fill=INK,width=4)
    elif kind == "priority_cards":
        for i,dx in enumerate((-70,0,70)):
            draw.rounded_rectangle((cx+dx-55,cy-70+i*14,cx+dx+20,cy+70+i*14),radius=8,fill=PALE if i==0 else "white",outline=INK,width=5)
    elif kind == "dumbbell":
        draw.line((cx-110,cy,cx+110,cy),fill=INK,width=15)
        for dx in (-105,-75,75,105): draw.line((cx+dx,cy-55,cx+dx,cy+55),fill=INK,width=13)
    elif kind in {"chair","gym_bench"}:
        draw.rounded_rectangle((cx-95,cy-90,cx-40,cy+35),radius=10,fill=PALE,outline=INK,width=6)
        draw.line((cx-75,cy+35,cx+100,cy+35),fill=INK,width=12)
        draw.line((cx+75,cy+35,cx+75,cy+105),fill=INK,width=8)
    elif kind in {"progress_bar","bag","mat"}:
        draw.rounded_rectangle((cx-120,cy-45,cx+120,cy+45),radius=18,fill="white",outline=INK,width=7)
        draw.rounded_rectangle((cx-110,cy-35,cx+25,cy+35),radius=10,fill=YELLOW)
    elif kind in {"night_window","window","mirror"}:
        draw.rectangle((cx-100,cy-100,cx+100,cy+100),fill=PALE,outline=INK,width=7)
        draw.line((cx,cy-100,cx,cy+100),fill=INK,width=5)
        if kind=="night_window": draw.ellipse((cx+25,cy-60,cx+65,cy-20),fill=YELLOW)
    elif kind in {"habit_loop","reward","attention","focus"}:
        draw.ellipse((cx-95,cy-95,cx+95,cy+95),fill=PALE,outline=INK,width=8)
        if kind=="habit_loop":
            draw.arc((cx-65,cy-65,cx+65,cy+65),30,310,fill=INK,width=10)
            draw.polygon([(cx+54,cy-57),(cx+88,cy-52),(cx+72,cy-23)],fill=INK)
        elif kind=="reward": draw.polygon([(cx,cy-70),(cx+20,cy-20),(cx+75,cy-20),(cx+30,cy+15),(cx+47,cy+70),(cx,cy+35),(cx-47,cy+70),(cx-30,cy+15),(cx-75,cy-20),(cx-20,cy-20)],fill=YELLOW)
        else: draw.ellipse((cx-45,cy-45,cx+45,cy+45),outline=INK,width=8)
    elif kind == "hourglass":
        draw.line((cx-80,cy-100,cx+80,cy-100),fill=INK,width=8); draw.line((cx-80,cy+100,cx+80,cy+100),fill=INK,width=8)
        draw.polygon([(cx-65,cy-90),(cx+65,cy-90),(cx,cy),(cx+65,cy+90),(cx-65,cy+90),(cx,cy)],fill=PALE,outline=INK)
    elif kind in {"behavior","person","walking","exercise"}:
        draw.ellipse((cx-25,cy-105,cx+25,cy-55),fill=PALE,outline=INK,width=5)
        draw.line((cx,cy-50,cx,cy+60),fill=INK,width=9)
        draw.line((cx,cy-10,cx-65,cy+20),fill=INK,width=8); draw.line((cx,cy-10,cx+65,cy+20),fill=INK,width=8)
        draw.line((cx,cy+60,cx-50,cy+105),fill=INK,width=8); draw.line((cx,cy+60,cx+55,cy+105),fill=INK,width=8)
    elif kind == "environment":
        draw.polygon([(cx-130,cy-30),(cx,cy-115),(cx+130,cy-30)],fill=PALE,outline=INK)
        draw.rectangle((cx-110,cy-30,cx+110,cy+105),fill="white",outline=INK,width=7)
        draw.rectangle((cx+15,cy+10,cx+75,cy+105),fill=PALE,outline=INK,width=5)
    elif kind == "social_media":
        draw.rounded_rectangle((cx-85,cy-110,cx+85,cy+110),radius=15,fill="white",outline=INK,width=8)
        for dy in (-65,-10,45): draw.rounded_rectangle((cx-60,cy+dy,cx+60,cy+dy+30),radius=5,fill=PALE)
    elif kind in {"alarm_clock", "timer"}:
        draw.ellipse((cx-90,cy-90,cx+90,cy+90),fill="white",outline=INK,width=9)
        draw.line((cx,cy,cx,cy-55),fill=INK,width=8); draw.line((cx,cy,cx+43,cy+22),fill=INK,width=8)
        if kind=="alarm_clock":
            draw.arc((cx-115,cy-125,cx-30,cy-40),180,330,fill=YELLOW,width=10)
    elif kind in {"calendar", "checklist"}:
        draw.rounded_rectangle((cx-115,cy-110,cx+115,cy+105),radius=16,fill="white",outline=INK,width=8)
        draw.rectangle((cx-111,cy-105,cx+111,cy-58),fill=PALE)
        for i in range(3):
            yy=cy-22+i*50
            if kind=="checklist":
                draw.rectangle((cx-85,yy,cx-56,yy+28),outline=INK,width=4)
                if i==0: draw.line((cx-80,yy+12,cx-68,yy+24,cx-46,yy-2),fill=YELLOW,width=6)
                draw.line((cx-35,yy+15,cx+80,yy+15),fill=INK,width=4)
            else:
                for j in range(3): draw.rounded_rectangle((cx-78+j*55,yy,cx-45+j*55,yy+30),radius=4,fill=PALE,outline=INK,width=3)
    elif kind in {"phone", "laptop"}:
        if kind=="phone":
            draw.rounded_rectangle((cx-65,cy-115,cx+65,cy+115),radius=18,fill="white",outline=INK,width=8)
            draw.rounded_rectangle((cx-45,cy-80,cx+45,cy+65),radius=6,fill=PALE)
        else:
            draw.rounded_rectangle((cx-130,cy-95,cx+130,cy+70),radius=10,fill="white",outline=INK,width=8)
            draw.rectangle((cx-105,cy-70,cx+105,cy+45),fill=PALE)
            draw.line((cx-155,cy+90,cx+155,cy+90),fill=INK,width=13)
    elif kind in {"ram", "server"}:
        if kind=="ram":
            draw.rounded_rectangle((cx-145,cy-52,cx+145,cy+52),radius=9,fill="white",outline=INK,width=8)
            for i in range(5):
                draw.rectangle((cx-115+i*48,cy-25,cx-80+i*48,cy+24),fill=PALE,outline=INK,width=3)
                draw.line((cx-110+i*48,cy+52,cx-110+i*48,cy+70),fill=YELLOW,width=8)
        else:
            draw.rounded_rectangle((cx-100,cy-125,cx+100,cy+125),radius=13,fill="white",outline=INK,width=8)
            for i in range(3):
                yy=cy-95+i*70
                draw.rounded_rectangle((cx-80,yy,cx+80,yy+48),radius=5,fill=PALE,outline=INK,width=4)
                draw.rectangle((cx+48,yy+17,cx+60,yy+29),fill=YELLOW)
    elif kind=="factory":
        draw.polygon([(cx-145,cy+95),(cx-145,cy-35),(cx-45,cy+10),(cx-45,cy-35),
                      (cx+55,cy+10),(cx+55,cy-35),(cx+145,cy+10),(cx+145,cy+95)],fill=PALE)
        draw.line((cx-145,cy+95,cx+145,cy+95),fill=INK,width=10)
        for dx in (-90,0,90): draw.rectangle((cx+dx-18,cy+45,cx+dx+18,cy+75),outline=INK,width=4)
    elif kind=="bed":
        draw.rounded_rectangle((cx-125,cy-25,cx+125,cy+55),radius=13,fill=PALE,outline=INK,width=7)
        draw.rounded_rectangle((cx-100,cy-55,cx-25,cy-15),radius=12,fill="white",outline=INK,width=5)
        draw.line((cx-130,cy-90,cx-130,cy+95),fill=INK,width=9)
    elif kind=="desk":
        draw.line((cx-130,cy+15,cx+130,cy+15),fill=INK,width=15)
        draw.line((cx-105,cy+20,cx-105,cy+100),fill=INK,width=8)
        draw.line((cx+105,cy+20,cx+105,cy+100),fill=INK,width=8)
        draw.rounded_rectangle((cx-50,cy-85,cx+50,cy+10),radius=8,fill=PALE,outline=INK,width=5)
    elif kind=="book":
        draw.polygon([(cx,cy-80),(cx-120,cy-100),(cx-120,cy+85),(cx,cy+105)],fill="white",outline=INK)
        draw.polygon([(cx,cy-80),(cx+120,cy-100),(cx+120,cy+85),(cx,cy+105)],fill=PALE,outline=INK)
        draw.line((cx,cy-80,cx,cy+105),fill=INK,width=6)
    elif kind=="price":
        draw.rounded_rectangle((cx-90,cy-105,cx+90,cy+105),radius=12,fill=PALE,outline=INK,width=8)
        draw.line((cx,cy+45,cx,cy-50),fill=YELLOW,width=12)
        draw.polygon([(cx,cy-85),(cx-35,cy-38),(cx+35,cy-38)],fill=YELLOW)
    elif kind=="water":
        draw.polygon([(cx-65,cy-95),(cx+65,cy-95),(cx+48,cy+90),(cx-48,cy+90)],fill="white",outline=INK)
        draw.rectangle((cx-49,cy+10,cx+49,cy+80),fill=(207,228,237))
    else:
        draw.rounded_rectangle((cx-100,cy-90,cx+100,cy+90),radius=16,fill=PALE,outline=INK,width=7)


def compose_assets(beat: dict, output_path: Path, assets_dir: Path = ASSETS_DIR) -> None:
    image = Image.new("RGBA", SIZE, (250, 249, 245, 255))
    draw = ImageDraw.Draw(image)
    if beat.get("visual_concept")=="not_a_toxin":
        draw.rounded_rectangle((220,190,1828,930),radius=42,fill="white",outline=(225,222,213),width=6)
        draw.rounded_rectangle((300,300,940,810),radius=32,fill=(255,245,241))
        draw.rounded_rectangle((1100,300,1740,810),radius=32,fill=(241,248,244))
        _icon(draw,"poison_bottle",(415,385,735,675))
        _icon(draw,"reset_x",(690,385,1010,675))
        _icon(draw,"brain",(1250,385,1570,675))
        draw.text((488,720),"NOT A TOXIN",font=_font(48),fill=(160,62,60))
        draw.text((1198,720),"BRAIN SIGNAL",font=_font(48),fill=INK)
        draw.line((990,555,1060,555),fill=YELLOW,width=13)
        draw.polygon([(1080,555),(1050,533),(1050,577)],fill=YELLOW)
        output_path.parent.mkdir(parents=True,exist_ok=True)
        image.convert("RGB").save(output_path)
        return
    if beat.get("scene_mode")=="host" and beat.get("environment")!="simple presentation space":
        draw.line((0,880,2048,880),fill=(225,220,207),width=8)
        if "bedroom" in beat["environment"] or "study" in beat["environment"]:
            draw.rectangle((1710,145,1935,415),fill=(235,240,241),outline=(177,184,186),width=8)
            draw.line((1822,145,1822,415),fill=(177,184,186),width=5)
    objects = beat.get("visual_objects") or [{"type":"idea"}]
    objects = objects[:5]
    arch = beat.get("visual_archetype", "example")
    count = len(objects)
    if count == 1:
        centers=[(1120,535)]
    elif count == 2:
        centers=[(660,500),(1430,500)]
    elif count == 3:
        centers=[(510,510),(1030,510),(1550,510)]
    else:
        centers=[(550,390),(1050,390),(1550,390),(800,780),(1350,780)][:count]
    if beat.get("visual_layout")=="vertical" and count<=3:
        centers=[(1120,260+i*300) for i in range(count)]
    elif beat.get("visual_layout")=="triangle" and count==3:
        centers=[(750,350),(1450,350),(1100,770)]
    elif beat.get("visual_layout")=="focus" and count>=2:
        centers=[(1070,360)]+[(550+i*500,790) for i in range(count-1)]
    for obj,(cx,cy) in zip(objects,centers):
        kind=str(obj.get("type", "object")).lower().replace(" ","_")
        group=GROUPS.get(kind,"misc")
        path=assets_dir/group/f"{kind}.png"
        if path.is_file():
            with Image.open(path) as source:
                source=source.convert("RGBA")
                source.thumbnail((320,290),Image.Resampling.LANCZOS)
                image.alpha_composite(source,(cx-source.width//2,cy-source.height//2))
        else:
            _icon(draw,kind,(cx-160,cy-145,cx+160,cy+145))
        labels={"notification":"CUE","reward":"REWARD","reset_x":"NO RESET",
                "habit_loop":"ROUTINE","behavior":"BEHAVIOR","environment":"ENVIRONMENT"}
        label=("ACTION" if kind=="phone" and beat.get("visual_relationship")=="sequence"
               else labels.get(kind,kind.replace("_"," ").upper()))[:18]
        if beat.get("scene_mode")!="host":
            font=_font(31)
            bbox=draw.textbbox((0,0),label,font=font)
            draw.text((cx-(bbox[2]-bbox[0])//2,cy+155),label,font=font,fill=INK)
    if count >= 2 and (arch in {"cause_effect", "process", "supply_flow", "timeline"} or beat.get("visual_relationship")=="sequence"):
        for (x1,y1),(x2,y2) in zip(centers,centers[1:]):
            if abs(y2-y1)>200: continue
            start=x1+205; end=x2-205
            if end>start:
                draw.line((start,y1,end,y2),fill=YELLOW,width=11)
                draw.polygon([(end,y2),(end-25,y2-17),(end-25,y2+17)],fill=YELLOW)
    if count==2 and arch=="comparison":
        draw.line((1040,270,1040,800),fill=(225,222,213),width=5)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    image.convert("RGB").save(output_path)
