from __future__ import annotations

import math

from bdbox import Choice, Int, Model, Preset
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
    Color,
    Compound,
    CounterBoreHole,
    CounterSinkHole,
    GridLocations,
    Line,
    Locations,
    Mode,
    Polyline,
    RotationLike,
    chamfer,
    extrude,
    fillet,
    make_face,
)


class HandleOutline(BaseSketchObject):
    def __init__(
        self,
        length: float,
        height: float,
        angle: float,
        resize: float = 0,
        adjust_for_thickness: float = 0,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                sub = (height + resize) * math.tan(angle * (math.pi / 180))
                lengthsub = 0.0
                if adjust_for_thickness:
                    lengthsub = (
                        -adjust_for_thickness
                        / 1
                        * math.tan(angle * (math.pi / 180))
                    )
                Line((-resize, 0), (length + lengthsub + resize, 0))
                ln = Polyline(
                    (length + lengthsub + resize, 0),
                    (length + lengthsub + resize - sub, height + resize),
                    (-resize + sub, height + resize),
                    (-resize, 0),
                )
                fillet(ln.vertices()[1:-1], radius=height / 2 + resize)
            make_face()
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class HandleBody(BasePartObject):
    def __init__(
        self,
        length: float,
        height: float,
        angle: float,
        thickness: float = 1 / 2 * IN,
        grip_thickness: float = 1 / 2 * IN,
        rotation: RotationLike = (90, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.MIN,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch():
                HandleOutline(
                    length=length,
                    height=height,
                    angle=angle,
                    resize=grip_thickness * (3 / 4),
                )
                with BuildSketch(mode=Mode.SUBTRACT):
                    HandleOutline(
                        adjust_for_thickness=thickness,
                        length=length,
                        height=height,
                        angle=angle,
                        resize=-grip_thickness * (1 / 4),
                    )
            extrude(amount=thickness)
            for i in [-1, 0]:
                chamfer(
                    p.edges().group_by(Axis.Z)[i].sort_by(Axis.Y)[2:],
                    thickness / 6,
                )

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ScrewHandle(Model):
    length: float = 6
    height: float = 1 + 1 / 4
    thickness: float = 1 / 2
    angle: float = 20
    screw_size: float = 3 / 16
    screw_style: str = Choice(
        "counter_sink", choices=("counter_sink", "counter_bore")
    )
    screw_hole_depth: float = 0
    screw_hole_countersink_angle: float = 60
    alpha: int = Int(0xCC, min=0x88, max=0xFF, step=1)
    presets = (
        Preset(
            "tray",
            screw_hole_depth=(1 / 4 + 1 / 16),
            screw_size=(9 / 64),
            screw_hole_countersink_angle=0,
        ),
        Preset("thin", screw_size=(9 / 64), thickness=(9 / IN) * MM),
    )

    def build(self) -> Compound:
        with BuildPart() as p:
            HandleBody(
                length=self.length * IN,
                height=self.height * IN,
                angle=self.angle,
                thickness=self.thickness * IN,
            )
            with (
                GridLocations(self.length * IN, 0, 2, 1),
                Locations(
                    (
                        0,
                        0,
                        (self.screw_hole_depth * IN) or (self.height * IN) / 2,
                    )
                ),
            ):
                if self.screw_style == "counter_sink":
                    kwargs = {}
                    if self.screw_hole_countersink_angle:
                        kwargs["counter_sink_angle"] = (
                            self.screw_hole_countersink_angle
                        )
                    CounterSinkHole(
                        radius=(self.screw_size * IN) / 2,
                        counter_sink_radius=(self.screw_size * IN),
                        mode=Mode.SUBTRACT,
                        **kwargs,
                    )
                elif self.screw_style == "counter_bore":
                    CounterBoreHole(
                        radius=(self.screw_size * IN) / 2,
                        counter_bore_radius=(self.screw_size * IN),
                        counter_bore_depth=0,
                        mode=Mode.SUBTRACT,
                    )
        p.part.label = "handle"
        p.part.color = Color(0x00BBFF, alpha=self.alpha)
        return p.part
