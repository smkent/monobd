from __future__ import annotations

from bdbox import Model
from build123d import Align, Axis, BuildPart, Cylinder, Plane, Select, fillet


class ModelAirplaneStand(Model):
    def build(self) -> Model.Geometry | None:
        with BuildPart() as p:
            Cylinder(16 * 2, 4, align=(Align.CENTER, Align.CENTER, Align.MAX))
            fillet(p.edges().filter_by(Plane.XY).sort_by(Axis.Z)[1], 1)
            Cylinder(16 / 2, 60, align=(Align.CENTER, Align.CENTER, Align.MIN))
            fillet(
                p.edges(Select.LAST).filter_by(Plane.XY).sort_by(Axis.Z)[0],
                4,
            )
            fillet(p.edges().filter_by(Plane.XY).sort_by(Axis.Z)[-1], 2)
        return p
