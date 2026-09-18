from pathlib import Path
from core.mock_service import MockService
from core.render import composite_scene, write_srt, render_scene
from core.utils import media_duration
from core.character_pose_selector import select_pose
from core.visual_beats import plan_visual_beats
from core.overlays import normalize_overlays
from PIL import Image
from unittest.mock import patch

def main():
    svc=MockService()
    td=Path(__file__).parent/'projects'/'smoke_test'; td.mkdir(parents=True,exist_ok=True)
    bg=td/'bg.png'; comp=td/'comp.jpg'; wav=td/'a.wav'; srt=td/'a.srt'
    svc.generate_background('demo',bg)
    composite_scene(bg,comp,True,'left',0.45,'surprised','question',['question_mark','exclamation'])
    svc.tts('Why is this suddenly so expensive? Here is the simple reason.',wav)
    dur=media_duration(wav); assert 2 < dur < 20, dur
    write_srt([{'narration':'Why is this suddenly so expensive? Here is the simple reason.','duration':dur}],srt)
    content=srt.read_text(encoding='utf-8'); assert '00:00:' in content and '24:51:' not in content
    assert content.count('-->') >= 2
    second=td/'second.jpg'; composite_scene(bg,second,False,'right',0.45)
    video=td/'motion.mp4'
    render_scene([comp,second],wav,video,dur,30,'zoom_in',beats=[
        {'duration':dur/2,'camera':'push_in','focus_side':'right','camera_strength':0.05},
        {'duration':dur/2,'camera':'pan_left','focus_side':'left','camera_strength':0.04}])
    assert video.exists() and video.stat().st_size>1000
    assert bg.exists() and comp.exists() and wav.exists()
    assert select_pose('surprised','react','question_reveal')[1]
    with patch('core.character_pose_selector.ASSETS_DIR',td/'empty_assets'):
        assert not select_pose('happy','celebrate','takeaway')[1]
    long_scene={'scene_id':10,'narration':('RAM is built from DRAM, used in PCs, phones and servers. '
        'AI servers need enormous pools of it, so manufacturers shift factory capacity toward server memory. '
        'That leaves fewer chips for ordinary buyers.'),'visual_archetype':'example'}
    assert len(plan_visual_beats(long_scene)) >= 4
    plain=td/'plain.png'; Image.new('RGB',(1920,1080),'white').save(plain)
    no_line=td/'no_connector.jpg'
    composite_scene(plain,no_line,True,'left',0.3,'explaining','point',[],
                    character_action='point_at_focus',focus_side='right',visual_archetype='example',
                    character_pose='explaining')
    with Image.open(no_line) as frame:
        center_region=frame.crop((700,430,1150,660))
        assert all(r>245 and g>245 and b>245 for r,g,b in center_region.get_flattened_data()), 'Long connector detected'
    clean=td/'clean.jpg'
    composite_scene(plain,clean,False,'left',0.3,overlay_symbols=[],focus_side='right',
                    on_screen_emphasis='Start here tomorrow',visual_archetype='question_reveal')
    with Image.open(clean) as frame:
        assert all(min(rgb)>245 for rgb in frame.crop((800,40,1120,145)).get_flattened_data()), 'Floating top label detected'
        assert all(min(rgb)>245 for rgb in frame.crop((1360,300,1640,590)).get_flattened_data()), 'Decorative ring detected'
    assert normalize_overlays(['spotlight','sparkle','question_mark'],'question_reveal',True) == [
        {'type':'question_mark','target':'character'}]
    assert normalize_overlays(['warning_mark'],'consequence',True)[0]['type']=='warning_mark'
    assert normalize_overlays([{'type':'check_mark','target':'focus_object'}],'takeaway',True)[0]['type']=='check_mark'
    for symbol,arch in [('question_mark','question_reveal'),('warning_mark','consequence'),('check_mark','takeaway')]:
        marked=td/f'{symbol}.jpg'
        composite_scene(plain,marked,True,'left',0.3,'curious','none',
            [{'type':symbol,'target':'focus_object'}],focus_side='right',visual_archetype=arch,
            character_pose='curious')
        assert marked.exists() and marked.stat().st_size>1000
    print('V3 SMOKE TEST OK')
if __name__=='__main__': main()
