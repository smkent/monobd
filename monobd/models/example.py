from functools import cached_property

from build123d import Color, Compound, Location

from ..common import BaseModel
from ..parts.example import ExamplePart


class Model(BaseModel):
    @cached_property
    def model(self) -> Compound:
        bp = ExamplePart()
        bp.label = "orange_box"
        bp.color = Color(0xFF8822, alpha=0x99)
        bp2 = ExamplePart().move(Location((20, 0, 0)))
        bp2.label = "green_box"
        bp2.color = Color(0x00CC22, alpha=0xCC)
        return Compound(label="example", children=[bp, bp2])  # type: ignore
