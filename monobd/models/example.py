from __future__ import annotations

from bdbox import Model, Preset
from build123d import (
    Align,
    Box,
    BuildPart,
    Color,
    Compound,
    Locations,
    chamfer,
    fillet,
)


class ExampleModel(Model):
    height_factor: int = 1
    presets = (Preset("tall", height_factor=2),)

    def build(self) -> Compound:
        with BuildPart() as p:
            Box(
                10,
                20,
                30 * self.height_factor,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            fillet(p.edges(), radius=2)
        p.part.label = "orange_box"
        p.part.color = Color(0xFF8822, alpha=0x99)
        with BuildPart() as p2, Locations((10, 0, 0)):
            Box(
                10,
                20,
                20 * self.height_factor,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            chamfer(p2.edges(), length=2)
        p2.part.label = "green_box"
        p2.part.color = Color(0x00CC22, alpha=0xCC)
        return Compound(label="example", children=[p.part, p2.part])
