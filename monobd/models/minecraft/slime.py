from __future__ import annotations

from functools import cached_property
from typing import ClassVar

from bdbox import Model, Preset
from build123d import (
    IN,
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    Box,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rectangle,
    RotationLike,
    Select,
    Vector,
    chamfer,
    extrude,
    offset,
    scale,
)


class SlimeFaceProfile(BaseSketchObject):
    def __init__(
        self,
        scale_factor: float = 1,
        fit: float = 0,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.MIN, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        rel_align = (Align.MIN, Align.MIN)
        eyes_size = 0.375 * IN
        mouth_size = Vector(0.25 * IN, 0.25 * IN)
        sep = Vector(0.812 * IN, 0.5625 * IN)
        with BuildSketch() as sk:
            with Locations(Pos(0, sep.Y), Pos(sep.X, sep.Y)):
                Rectangle(eyes_size, eyes_size, align=rel_align)
            with Locations(Pos(sep.X, 0)):
                Rectangle(mouth_size.X, mouth_size.Y, align=rel_align)
            if scale_factor != 1:
                scale(by=scale_factor)
            if fit > 0:
                offset(amount=-fit)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class SlimeFace(BasePartObject):
    FACE_DEPTH = 0.2 * IN

    def __init__(
        self,
        scale_factor: float = 1,
        fit: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (Align.MIN, Align.MIN, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch():
                SlimeFaceProfile(scale_factor=scale_factor, fit=fit)
            extrude(amount=self.FACE_DEPTH * scale_factor)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class Slime(Model):
    scale_factor: float = 1

    corner_radius: float = 0.8
    face_fit: float = 0.2

    FACE_POS: ClassVar[Vector] = Vector(0.1875 * IN, 0.25 * IN)
    BODY_SIZE: ClassVar[Vector] = Vector(1.625 * IN, 1.5 * IN, 1.52 * IN)

    presets = (
        Preset("small", scale_factor=0.85),
        Preset("regular", scale_factor=1),
        Preset("large", scale_factor=1.4),
    )

    @cached_property
    def face_pos(self) -> Pos:
        return Pos(
            self.FACE_POS.X * self.scale_factor,
            self.FACE_POS.Y * self.scale_factor,
        )

    def build(self) -> Model.Geometry | None:
        return Compound(children=[self.body(), self.face()], label="slime")

    def body(self) -> Compound:
        with BuildPart() as p:
            Box(
                self.BODY_SIZE.X * self.scale_factor,
                self.BODY_SIZE.Y * self.scale_factor,
                self.BODY_SIZE.Z * self.scale_factor,
                align=(Align.MIN, Align.MIN, Align.MIN),
            )
            if not p.part:
                raise RuntimeError("Empty part")
            if self.corner_radius > 0:
                chamfer(p.edges(), self.corner_radius)
            with Locations(
                Pos(0, 0, p.part.bounding_box().max.Z) * self.face_pos
            ):
                SlimeFace(
                    align=(Align.MIN, Align.MIN, Align.MAX),
                    scale_factor=self.scale_factor,
                    mode=Mode.SUBTRACT,
                )
            chamfer(
                p.edges(Select.LAST).filter_by(Plane.XY).group_by(Axis.Z)[-1],
                0.2,
            )
        p.part.label = "body"
        p.part.color = Color(0x006600)
        return p.part

    def face(self) -> Part:
        with (
            BuildPart() as p,
            Locations(
                self.face_pos
                * Pos(
                    0,
                    0,
                    (self.BODY_SIZE.Z - SlimeFace.FACE_DEPTH)
                    * self.scale_factor,
                )
                * Pos(self.face_fit, self.face_fit)
            ),
        ):
            SlimeFace(scale_factor=self.scale_factor, fit=self.face_fit)
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "face"
        p.part.color = Color("black")
        return p.part
