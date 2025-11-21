from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any

from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    CounterSinkHole,
    Cylinder,
    GridLocations,
    Locations,
    Mode,
    Plane,
    PolarLocations,
    Rectangle,
    RectangleRounded,
    chamfer,
    extrude,
    loft,
)

from ...common import Model


@dataclass
class EMTExtension(Model, name="emt_extension"):
    diameter: float = (1 + 0 / 4) * IN
    thickness: float = (1 + 1 / 8) * IN
    screw_size: float = (1 / 4) * IN
    chamfer: float = (1 / 8) * IN
    slop: float = (1 / 32) * IN

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {"default": {}}

    @cached_property
    def assembly(self) -> Compound:
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
            chamfer(p.edges().group_by(Axis.Z)[:], self.chamfer)
        p.part.label = "emt_extension"
        p.part.color = Color(0x11AA88, alpha=0xCC)
        return Compound(label=self.model_name, children=[p.part])
