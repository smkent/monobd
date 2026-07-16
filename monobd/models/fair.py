from __future__ import annotations

from bdbox import Inches, Model
from build123d import (
    IN,
    MM,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    CounterSinkHole,
    Cylinder,
    GridLocations,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    chamfer,
    extrude,
)


class ShelfFoot(Model):
    diameter: float = Inches(3 / 4)
    length: float = Inches(4)
    thickness: float = Inches(1 / 2)
    screw_size: float = Inches(3 / 16)
    slop: float = Inches(1 / 32)

    def build(self) -> Model.Geometry:
        width = self.diameter + self.screw_size * 6
        spread = width - self.screw_size * 3
        screw_rows = 2 if self.length > self.screw_size * 8 else 1
        with BuildPart() as p:
            with BuildSketch():
                RectangleRounded(self.length, width, (1 / 4) * IN)
            extrude(amount=self.thickness)
            Cylinder(
                radius=(self.diameter + self.slop) / 2,
                height=self.length,
                rotation=(0, 90, 0),
                mode=Mode.SUBTRACT,
            )
            cutout_len = self.length - self.screw_size * 6
            if cutout_len > 0:
                with BuildSketch():
                    RectangleRounded(
                        cutout_len,
                        width - self.screw_size * 3,
                        (1 / 4) * IN,
                    )
                extrude(amount=self.thickness, mode=Mode.SUBTRACT)
            chamfer(
                p.edges(),
                (1 / 32 / 1.01) * IN,
            )
            with (
                Locations(-Plane.XY),
                GridLocations(
                    self.length - self.screw_size * 3, spread, screw_rows, 2
                ),
            ):
                CounterSinkHole(
                    radius=self.screw_size / 2,
                    counter_sink_radius=self.screw_size,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "shelf-foot"
        p.part.color = Color(0x33CC66, alpha=0xCC)
        return Compound(label="fair_shelf_foot", children=[p.part])


class PictureFrame(Model):
    length: float = Inches(11)
    width: float = Inches(8.5 / 2)
    frame_thick: float = Inches(1 / 4)
    thickness: float = 5 * MM

    def build(self) -> Model.Geometry:
        with BuildPart() as p:
            with BuildSketch():
                RectangleRounded(
                    self.length + self.frame_thick * 2,
                    self.width + self.frame_thick * 2,
                    (1 / 4) * IN,
                )
                Rectangle(
                    self.length - self.frame_thick * 2,
                    self.width - self.frame_thick * 2,
                    mode=Mode.SUBTRACT,
                )
            extrude(amount=self.thickness)
            with BuildSketch():
                Rectangle(
                    self.length,
                    self.width,
                )
            extrude(amount=self.thickness / 2, mode=Mode.SUBTRACT)
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "picture-frame"
        p.part.color = Color(0x3399CC, alpha=0xCC)
        return Compound(label="fair_picture_frame", children=[p.part])
