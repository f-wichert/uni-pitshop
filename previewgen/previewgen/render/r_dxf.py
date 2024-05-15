import ezdxf
import ezdxf.audit
import ezdxf.document
import ezdxf.recover
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.properties import LayoutProperties

from ._base import Renderer


class RendererDXF(Renderer):
    def _render_internal(self) -> None:
        try:
            # try fast path first
            doc = ezdxf.readfile(self.path)
            auditor = doc.audit()
        except Exception as e:
            if isinstance(e, IOError):
                raise
            doc, auditor = ezdxf.recover.readfile(self.path)

        if auditor.has_errors:
            errors = "\n".join(
                f"\t[{error.code}] in {error.entity!s}: {error.message}" for error in auditor.errors
            )
            raise ezdxf.DXFError(f"unable to read {self.path}; auditor found errors:\n{errors}")

        modelspace = doc.modelspace()
        layout_properties = LayoutProperties.from_layout(modelspace)
        layout_properties.set_colors("#ffffff")

        ctx = RenderContext(doc)
        Frontend(ctx, self.backend).draw_layout(
            doc.modelspace(), finalize=False, layout_properties=layout_properties
        )
