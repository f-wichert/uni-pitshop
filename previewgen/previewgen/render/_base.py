import contextlib
import io
from abc import ABC, abstractmethod
from typing import Iterator

import matplotlib.axes as mpa  # type: ignore
import matplotlib.figure as mpf  # type: ignore
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend


class Renderer(ABC):
    fig: mpf.Figure
    ax: mpa.Axes
    backend: MatplotlibBackend

    def __init__(self, path: str):
        self.path = path

    def render(self) -> io.BytesIO:
        with self._create_fig():
            self._render_internal()

        stream = io.BytesIO()
        self.fig.savefig(stream, format="png")
        stream.seek(0)
        return stream

    @contextlib.contextmanager
    def _create_fig(self) -> Iterator[None]:
        assert not hasattr(self, "fig")  # prevent reuse
        self.fig = mpf.Figure()
        self.ax: mpa.Axes = self.fig.add_axes([0, 0, 1, 1])
        self.backend = MatplotlibBackend(self.ax)  # (ab)using ezdxf backend for sane plot defaults
        try:
            yield
        finally:
            self.backend.finalize()  # type: ignore  # why

    @abstractmethod
    def _render_internal(self) -> None:
        raise NotImplementedError
