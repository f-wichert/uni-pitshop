from ._base import Renderer


class RendererDWG(Renderer):
    def _render_internal(self) -> None:
        raise NotImplementedError
