"""Image provider boundary; backgrounds never include the character reference."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Protocol


class ImageProvider(Protocol):
    def generate_image(self, prompt: str, output_path: Path, *, model: str,
                       quality: str, size: str) -> None: ...


class OpenAIImageProvider:
    def __init__(self, client):
        self.client = client

    def generate_image(self, prompt: str, output_path: Path, *, model: str,
                       quality: str, size: str) -> None:
        result = self.client.images.generate(model=model,prompt=prompt,quality=quality,
                                             size=size,output_format="png",background="opaque")
        data = result.data[0].b64_json
        if not data:
            raise RuntimeError("Image provider returned no image data")
        output_path.write_bytes(base64.b64decode(data))

    def edit_image(self, prompt: str, reference_path: Path, output_path: Path, *, model: str,
                   quality: str, size: str) -> None:
        with reference_path.open("rb") as reference:
            result = self.client.images.edit(model=model, image=reference, prompt=prompt,
                                             quality=quality, size=size, output_format="png")
        data = result.data[0].b64_json
        if not data:
            raise RuntimeError("Image provider returned no edited image data")
        output_path.write_bytes(base64.b64decode(data))
