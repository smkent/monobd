from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any

from build123d import Color, Compound, Location

from ..common import Model
from ..parts.example import ExamplePart


@dataclass
class ExampleModel(Model, name="example"):
    xoff: int = 20

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "default": {"xoff": 30},
            "wider": {"xoff": 50},
        }

    @cached_property
    def assembly(self) -> Compound:
        bp = ExamplePart()
        bp.label = "orange_box"
        bp.color = Color(0xFF8822, alpha=0x99)
        bp2 = ExamplePart().move(Location((self.xoff, 0, 0)))
        bp2.label = "green_box"
        bp2.color = Color(0x00CC22, alpha=0xCC)
        return Compound(  # type: ignore
            label=self.model_name, children=[bp, bp2]
        )
