from __future__ import annotations

from bdbox import Model
from build123d import (
    IN,
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    Mode,
    Plane,
    chamfer,
    loft,
)


class RGBLight(Model):
    diameter: float = (1 + 1 / 4) * IN
    thickness: float = (1 + 1 / 8) * IN
    screw_size: float = (1 / 4) * IN
    chamfer: float = (1 / 16) * IN
    slop: float = (1 / 32) * IN

    def build(self) -> Compound:
        with BuildPart() as p:
            with BuildSketch():
                Circle(self.diameter / 2)
            with BuildSketch(Plane.XY.offset(self.thickness)):
                Circle(self.diameter / 2)
            loft()
            Cylinder(
                (self.screw_size + self.slop) / 2,
                self.thickness,
                mode=Mode.SUBTRACT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            chamfer(p.edges().group_by(Axis.Z)[:], self.chamfer)
        p.part.label = "emt_extension"
        p.part.color = Color(0x11AA88, alpha=0xCC)
        return Compound(children=[p.part])
