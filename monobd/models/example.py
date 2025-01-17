from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any

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

from ..common import Model


@dataclass
class ExampleModel(Model, name="example"):
    height_factor: int = 1

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "default": {},
            "tall": {"height_factor": 2},
        }

    @cached_property
    def assembly(self) -> Compound:
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
        return Compound(  # type: ignore
            label=self.model_name, children=[p.part, p2.part]
        )
