from pathlib import Path
from uuid import uuid4
import base64
from types import SimpleNamespace
from PIL import Image

from core.asset_composer import compose_assets
from core.hybrid_image_engine import HybridImageEngine
from core.image_strategy import mode_limit, plan_visual_objects, select_image_strategy
from core.image_provider import OpenAIImageProvider


class FakeImages:
    def __init__(self):
        self.calls = []

    def generate_background(self, prompt, output_path, *, quality, size):
        self.calls.append((prompt, quality, size))
        Image.new("RGB",(64,64),(200,210,220)).save(output_path)


def main():
    root=Path(__file__).parent/"projects"/"hybrid_test"
    root.mkdir(parents=True,exist_ok=True)
    unique=uuid4().hex
    simple={"narration":"AI servers need RAM chips","focus_object":"server memory","visual_archetype":"cause_effect"}
    simple["visual_objects"]=plan_visual_objects(simple)
    assert {o["type"] for o in simple["visual_objects"]} >= {"server","ram"}
    assert select_image_strategy(simple)[0]=="asset_composer"
    abstract={"narration":"A surreal metaphor for information overload","visual_archetype":"myth_fact",
              "background_prompt":unique,"visual_objects":[]}
    assert select_image_strategy(abstract)[0]=="full_scene_ai"
    assert select_image_strategy(abstract,demo_mode=True)[0]=="character_composite"
    assert mode_limit("low_cost",4)==2 and mode_limit("balanced",4)==4 and mode_limit("high_quality",8)==8

    output=root/"missing_asset.png"
    compose_assets({**simple,"visual_objects":[{"type":"server"},{"type":"ram"}]},output,
                   assets_dir=root/"absent_assets")
    with Image.open(output) as image:
        assert image.size==(2048,1152)
        assert len(image.getcolors(maxcolors=1000000) or [])>2

    fake=FakeImages()
    engine=HybridImageEngine("low_cost",False,fake,cache_dir=root/"cache",global_limit=2)
    for i in range(3):
        beat={**abstract,"background_prompt":f"{unique} concept {i}","image_strategy":"ai_image",
              "image_strategy_reason":"complex metaphor","visual_objects":simple["visual_objects"]}
        engine.render_background(beat,root/f"ai_{i}.png",{})
        if i==2: assert beat["image_strategy"]=="asset_composer"
    assert engine.ai_image_calls==2 and engine.local_scenes==1 and len(fake.calls)==2
    assert all(len(args)==3 and unique in args[0] for args in fake.calls)
    assert all("NO PEOPLE. NO HUMAN FIGURES. NO CHARACTERS." in args[0] for args in fake.calls)

    first={**abstract,"background_prompt":f"{unique} concept 0","image_strategy":"ai_image",
           "image_strategy_reason":"complex metaphor"}
    entry={}
    engine.render_background(first,root/"cached.png",entry)
    assert entry["cache_hit"] and engine.ai_image_calls==2 and engine.cache_hits==1

    class FailingImages:
        def generate_background(self,*args,**kwargs):
            raise RuntimeError("simulated provider failure")
    failed=HybridImageEngine("balanced",False,FailingImages(),cache_dir=root/"cache",global_limit=4)
    beat={**abstract,"background_prompt":f"{unique} failure","image_strategy":"ai_image",
          "image_strategy_reason":"complex metaphor"}
    failed.render_background(beat,root/"fallback.png",{})
    assert beat["image_strategy"]=="asset_composer" and (root/"fallback.png").exists()

    class RecordingImages:
        def __init__(self): self.kwargs=None; self.edit_kwargs=None
        def generate(self, **kwargs):
            self.kwargs=kwargs
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"mock png bytes").decode())])
        def edit(self, **kwargs):
            self.edit_kwargs={k:v for k,v in kwargs.items() if k!="image"}
            assert kwargs["image"].read()==b"reference image"
            return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(b"edited bytes").decode())])
    recording=RecordingImages()
    provider=OpenAIImageProvider(SimpleNamespace(images=recording))
    provider.generate_image("simple empty classroom",root/"provider.png",
                            model="gpt-image-1-mini",quality="medium",size="1536x1024")
    assert (root/"provider.png").read_bytes()==b"mock png bytes"
    assert set(recording.kwargs)=={"model","prompt","quality","size","output_format","background"}
    reference=root/"reference.png"; reference.write_bytes(b"reference image")
    provider.edit_image("character at desk",reference,root/"edited.png",
                        model="gpt-image-1-mini",quality="medium",size="1536x1024")
    assert (root/"edited.png").read_bytes()==b"edited bytes"
    assert set(recording.edit_kwargs)=={"model","prompt","quality","size","output_format"}
    print("HYBRID IMAGE TEST OK")


if __name__=="__main__": main()
