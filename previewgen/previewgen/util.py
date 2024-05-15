import io
from typing import Dict, Type

from .render import Renderer, Renderer3DM, RendererDWG, RendererDXF

_format_map: Dict[str, Type[Renderer]] = {
    "3dm": Renderer3DM,
    "dwg": RendererDWG,
    "dxf": RendererDXF,
}


def render_file(path: str) -> io.BytesIO:
    if renderer_type := _format_map.get(path.rsplit(".", 1)[1]):
        r = renderer_type(path)
        return r.render()
    else:
        assert False, f"unknown file type: {path}"
