from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BaseSketchObject,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    GridLocations,
    Mode,
    Plane,
    RectangleRounded,
    Select,
    add,
    chamfer,
    extrude,
    fillet,
)

from monobd.common.model import Model
from monobd.objects import SVGSketch

from .assets import asset

CARD_WIDTH = 6 * IN
CARD_HEIGHT = 3.96 * IN
CARD_THICK = 1 * MM
CARD_FIT = 1 * MM
FRAME_THICK = 5 * MM
FRAME_HEIGHT = 2 * MM
CUTOUT_INSET = 9 * MM


class BackCutoutShape(BaseSketchObject):
    def __init__(
        self,
        width: float = CARD_WIDTH,
        height: float = CARD_HEIGHT,
        svg: str | None = None,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
        *,
        corner_holes: bool = True,
    ) -> None:
        hole_size = 0.325 * IN
        inset = 0.45 * IN
        with BuildSketch() as sk:
            RectangleRounded(
                width - CUTOUT_INSET,
                height - CUTOUT_INSET,
                hole_size,
            )
            if svg:
                svg_size = (min(width, height) - CUTOUT_INSET) * 1.18
                svg_sketch = SVGSketch(
                    file_name=asset(svg),
                    size=svg_size,
                    rotation=0,
                    flip_x=True,
                    mode=Mode.PRIVATE,
                )
                svg_x = svg_sketch.bounding_box().size.X * 1.1
                svg_copies = max(1, math.floor((width - CUTOUT_INSET) / svg_x))
                with GridLocations((svg_copies - 1) * svg_x, 0, svg_copies, 1):
                    add(svg_sketch, mode=Mode.SUBTRACT)
            gw = width - inset * 2
            gh = height - inset * 2
            grid_locs = GridLocations(gw, gh, 2, 2)
            if corner_holes:
                with grid_locs:
                    Circle(hole_size * 1.25, mode=Mode.SUBTRACT)
                fillet(sk.vertices(Select.LAST), radius=0.25 * IN)
                with grid_locs:
                    Circle(hole_size / 2)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class FrontCutoutShape(BaseSketchObject):
    def __init__(
        self,
        width: float = CARD_WIDTH,
        height: float = CARD_HEIGHT,
        fit: float = CARD_FIT,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            RectangleRounded(
                width + fit,
                height + fit,
                FRAME_THICK * 1.5,
            )
            circle_r = 0.5 * IN
            with GridLocations(
                (width - FRAME_THICK / 2) / (3 + 0.5),
                height + circle_r * 2 - 5 * MM,
                3,
                2,
            ):
                Circle(circle_r, mode=Mode.SUBTRACT)
            fillet(sk.vertices(Select.LAST), radius=0.5 * IN)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


@dataclass
class BikeCardModel(Model, name="bikecard"):
    style: str = "card"
    width: float = CARD_WIDTH
    height: float = CARD_HEIGHT
    svg: str | None = "immortan-joe.svg"

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "default": {},
            "bagtag": {
                "width": 3.75 * IN,
                "height": 1.55 * IN,
                "style": "bagtag",
            },
        }

    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            with BuildSketch():
                RectangleRounded(
                    self.width + FRAME_THICK * 2 + CARD_FIT,
                    self.height + FRAME_THICK * 2 + CARD_FIT,
                    FRAME_THICK * 2.5,
                )
            extrude(amount=FRAME_HEIGHT * 2 + CARD_THICK)
            chamfer(
                p.edges().group_by(Axis.Z)[:],
                1.0 * MM,
            )
            with BuildSketch():
                width = self.width
                if self.style == "bagtag":
                    width -= FRAME_THICK * 2
                BackCutoutShape(
                    width,
                    self.height,
                    svg=self.svg,
                    corner_holes=(self.style == "card"),
                )
            extrude(amount=FRAME_HEIGHT + CARD_THICK, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.XY.offset(FRAME_HEIGHT)):
                RectangleRounded(
                    self.width + CARD_FIT,
                    self.height + CARD_FIT,
                    CARD_FIT / 2,
                )
            extrude(amount=CARD_THICK, mode=Mode.SUBTRACT)
            with BuildSketch(Plane.XY.offset(FRAME_HEIGHT + CARD_THICK)):
                FrontCutoutShape(self.width, self.height, CARD_FIT)
            extrude(amount=FRAME_HEIGHT, mode=Mode.SUBTRACT)
        p.part.label = "frame"
        p.part.color = Color(0x3388FF, alpha=0xFF)
        return Compound(label=self.model_name, children=[p.part])
