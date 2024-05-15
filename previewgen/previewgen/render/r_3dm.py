import uuid
from typing import TYPE_CHECKING, Callable, Iterable, List, Tuple, TypeVar, cast

import numpy as np
import rhino3dm as r3

from ._base import Renderer

DIVISIONS = 100


class Renderer3DM(Renderer):
    def _render_internal(self) -> None:
        self.model = r3.File3dm.Read(self.path)
        self.objects = cast("R3File3dmObjectTable", self.model.Objects)
        self.defs = cast("R3File3dmInstanceDefinitionTable", self.model.InstanceDefinitions)

        # TODO: take layers into account
        for obj in self.objects:
            if obj.Attributes.IsInstanceDefinitionObject:
                continue
            self._handle_object(obj, [])

    def _handle_object(self, obj: r3.File3dmObject, transforms: List[r3.Transform]) -> None:
        assert len(transforms) <= 25  # limit recursion depth

        draw_color = obj.Attributes.DrawColor  # type: ignore
        color = tuple(x / 255 for x in draw_color(self.model)[:3])

        geo = obj.Geometry

        if isinstance(geo, r3.Curve):
            # draw curve
            points = list(self._curve_to_points(geo, transforms))
            pts = np.array(points, dtype=np.float64)
            self.ax.plot(pts[:, 0], pts[:, 1], linestyle="-", color=color)
        elif isinstance(geo, R3InstanceReference):
            # recursively draw referenced objects
            parent_id: uuid.UUID = geo.ParentIdefId
            ids = self.defs.FindId(parent_id).GetObjectIds()
            transforms.append(geo.Xform)
            for id in ids:
                self._handle_object(self.objects.FindId(id), transforms)
            transforms.pop()
        else:
            print(f"unknown geometry object {geo!r}")

    def _curve_to_points(
        self, geo: r3.Curve, transforms: List[r3.Transform]
    ) -> Iterable[Tuple[float, float]]:
        v3p = self._make_v3p(transforms) if transforms else self._v3p

        if isinstance(geo, r3.LineCurve):
            # untested
            yield from map(v3p, [geo.PointAtStart, geo.PointAtEnd])
        elif isinstance(geo, r3.PolylineCurve):
            yield from (v3p(geo.Point(i)) for i in range(geo.PointCount))
        elif isinstance(geo, r3.PolyCurve):
            # untested
            for segment in map(geo.SegmentCurve, range(geo.SegmentCount)):
                yield from self._curve_to_points(segment, transforms)
        else:
            domain = geo.Domain
            domain_len = domain.T1 - domain.T0
            for i in range(DIVISIONS):
                t = domain.T0 + (i / DIVISIONS) * domain_len
                yield v3p(geo.PointAt(t))

    @staticmethod
    def _v3p(v: r3.Point3d) -> Tuple[float, float]:
        return (v.X, v.Y)

    @classmethod
    def _make_v3p(
        cls, transforms: List[r3.Transform]
    ) -> Callable[[r3.Point3d], Tuple[float, float]]:
        def v3p(v: r3.Point3d) -> Tuple[float, float]:
            # this isn't really how transform matrices work, but meh
            for transform in reversed(transforms):
                # this does actually return the new point, stubs are wrong :/
                v = cast(r3.Point3d, v.Transform(transform))
            return cls._v3p(v)

        return v3p


if TYPE_CHECKING:
    # doesn't exist in the type stubs for some reason
    class R3InstanceDefinition(r3.CommonObject):
        Id: uuid.UUID
        Name: str
        Description: str

        def GetObjectIds(self) -> List[uuid.UUID]:
            ...

    T = TypeVar("T")

    class _R3Collection(Iterable[T]):
        def FindId(self, id: uuid.UUID) -> T:
            ...

    class R3File3dmInstanceDefinitionTable(
        r3.File3dmInstanceDefinitionTable, _R3Collection[R3InstanceDefinition]
    ):
        pass

    class R3File3dmObjectTable(r3.File3dmObjectTable, _R3Collection[r3.File3dmObject]):
        pass

    class R3InstanceReference(r3.InstanceReference):
        ParentIdefId: uuid.UUID
        Xform: r3.Transform


else:
    R3InstanceReference = r3.InstanceReference
