from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from operator import itemgetter
from typing import Any

from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    BuildLine,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    CounterSinkHole,
    GridLocations,
    Locations,
    Mode,
    Plane,
    Polyline,
    Rectangle,
    RotationLike,
    Select,
    ThreePointArc,
    chamfer,
    extrude,
    fillet,
    make_face,
    mirror,
)

from ...common import Model

first_and_last = itemgetter(0, -1)


class DispenserOutline(BaseSketchObject):
    def __init__(
        self,
        radius: float,
        length: float,
        thickness: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
    ):
        gap = (1 / 2) * IN
        with BuildSketch() as sk:
            Circle(radius=radius + thickness)
            Circle(radius=radius, mode=Mode.SUBTRACT)
            with Locations((0, -radius)):
                Rectangle(length, thickness, align=(Align.CENTER, Align.MAX))
            fillet(
                first_and_last(
                    sk.vertices()
                    .sort_by(Axis.Y)
                    .filter_by_position(Axis.X, -radius * 2, radius * 2)
                ),
                radius=radius / 2,
            )
            with Locations((0, -radius)):
                Rectangle(
                    gap,
                    radius * 2,
                    align=(Align.CENTER, Align.CENTER),
                    mode=Mode.SUBTRACT,
                )
            fillet(
                sk.vertices()
                .sort_by_distance((0, 0))
                .filter_by_position(Axis.X, -radius, radius)
                .filter_by_position(Axis.Y, -radius, radius),
                radius=thickness / 2,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class DispenserCutout(BasePartObject):
    def __init__(
        self,
        width: float,
        radius: float,
        rotation: RotationLike = (90, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        opening_length = (2 + 1 / 4) * IN
        opening_width = (1 / 2) * IN
        with BuildPart() as p:
            with BuildSketch() as sk:
                with BuildLine():
                    hl = (opening_length - opening_width) / 2
                    cutl = hl / 4
                    cutw = opening_width / 4
                    Polyline(
                        (0, hl),
                        (0, cutw + cutl),
                        (cutw, cutl),
                        (cutw, 0),
                        (opening_width - cutw, 0),
                        (opening_width - cutw, cutl),
                        (opening_width, cutl + cutw),
                        (opening_width, hl),
                    )
                    ThreePointArc(
                        (opening_width, hl),
                        (opening_width / 2, hl + opening_width / 2),
                        (0, hl),
                    )
                make_face()
                fillet(
                    sk.vertices()
                    .sort_by(Axis.Y)
                    .filter_by_position(
                        Axis.Y, 0, hl, inclusive=(False, False)
                    ),
                    radius=cutw,
                )
                mirror(sk.sketch, about=Plane.XZ)
            extrude(amount=radius * 2)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class DispenserBody(BasePartObject):
    def __init__(
        self,
        radius: float,
        length: float,
        width: float,
        thickness: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        with BuildPart() as p:
            with BuildSketch():
                DispenserOutline(
                    radius=radius, length=length, thickness=thickness
                )
            extrude(amount=width)
            fillet(
                p.edges()  # Select.LAST)
                .filter_by(Axis.Y)
                .sort_by_distance((0, 0, width / 2))[-4:],
                radius=(1 / 4) * IN,
            )
            chamfer(
                p.edges().filter_by_position(
                    Axis.Y, 0, width * 10, inclusive=(False, True)
                ),
                length=max(0.6 * MM, thickness / 10),
            )
            with Locations((0, radius * 2, width / 2)):
                DispenserCutout(width=width, radius=radius, mode=Mode.SUBTRACT)
            fillet(p.edges(Select.LAST), radius=1)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


@dataclass
class PoopBagDispenserWallMount(Model, name="poop_bag_dispenser_wall_mount"):
    diameter = 1.6 * IN
    length: float = 4 * IN
    width: float = (2 + 3 / 4) * IN
    thickness: float = (1 / 8 + 1 / 32) * IN
    screw_size: float = (3 / 16) * IN

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {"default": {}}

    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            DispenserBody(
                radius=self.diameter / 2,
                length=self.length,
                width=self.width,
                thickness=self.thickness,
                align=(Align.CENTER, Align.MIN, Align.CENTER),
                rotation=(90, 0, 0),
            )
            with (
                Locations((0, 0, self.thickness)),
                GridLocations((3 + 1 / 4) * IN, 2 * IN, 2, 2),
            ):
                CounterSinkHole(
                    radius=self.screw_size / 2,
                    counter_sink_radius=self.screw_size,
                )
        p.part.label = "dispenser"
        p.part.color = Color(0x33CC66, alpha=0xCC)
        return Compound(label=self.model_name, children=[p.part])
