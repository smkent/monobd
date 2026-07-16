from __future__ import annotations

from bdbox import Inches, Model
from build123d import (
    IN,
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Cylinder,
    Mode,
    Plane,
    chamfer,
    loft,
)


class EMTExtension(Model):
    diameter: float = Inches(1)
    thickness: float = Inches(1 + 1 / 8)
    screw_size: float = Inches(1 / 4)
    chamfer: float = Inches(1 / 8)
    slop: float = Inches(1 / 32)

    def build(self) -> Model.Geometry:
        with BuildPart() as p:
            with BuildSketch():
                Circle(self.diameter + 1 / 4 * IN * 0)
            with BuildSketch(Plane.XY.offset(self.thickness)):
                Circle(self.diameter)
            loft()
            Cylinder(
                (self.screw_size + self.slop) / 2,
                self.thickness,
                mode=Mode.SUBTRACT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            chamfer(list(p.edges().group_by(Axis.Z)), self.chamfer)
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "emt_extension"
        p.part.color = Color(0x11AA88, alpha=0xCC)
        return p.part
