from __future__ import annotations

from enum import Enum, auto
from math import floor

from bdbox import Inches, Model, Preset
from build123d import (
    IN,
    Align,
    BaseSketchObject,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    GridLocations,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    Select,
    extrude,
    fillet,
)

from monobd.objects.hatches import HatchPattern


class L(BaseSketchObject):
    def __init__(
        self,
        size: float,
        inset: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            Rectangle(size, size, align=(Align.MIN, Align.MIN))
            with Locations((inset, inset)):
                Rectangle(
                    size,
                    size,
                    align=(Align.MIN, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class CutoutType(Enum):
    NONE = auto()
    SQUARE = auto()
    HATCH = auto()


class RouterJig(Model):
    size: float = Inches(8)
    corner_radius: float = Inches(1)
    corner_space: float = Inches(2)
    thickness: float = 5
    span: float = Inches(2.5)
    grip: float = Inches(0.25)
    grip_height: float = Inches(0.75)
    round_corners: bool = True
    edge_guides: bool = True
    cutout_type: CutoutType = CutoutType.HATCH

    presets = (
        Preset(
            "1 inch",
            size=8,
            corner_radius=1,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
        Preset(
            "2 inch",
            size=9,
            corner_radius=2,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
        Preset(
            "3 inch",
            size=10,
            corner_radius=3,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
    )

    def build(self) -> Model.Geometry:
        corner_space = self.corner_space + self.corner_radius
        inset = self.span
        grip = self.grip if self.edge_guides else 0
        misc_spacing = max(1 / 8 * IN, self.grip or (inset / 8))
        misc_radius = misc_spacing / 2 if self.round_corners else 0
        with BuildPart() as p:
            with BuildSketch() as sk:
                L(self.size, inset + grip, align=(Align.MIN, Align.MIN))
                if self.edge_guides:
                    with Locations((0, 0)):
                        L(
                            corner_space,
                            grip,
                            mode=Mode.SUBTRACT,
                            align=(Align.MIN, Align.MIN),
                        )
                fillet(
                    sk.vertices().sort_by_distance((0, 0))[0],
                    radius=self.corner_radius,
                )
                pos = (inset + grip, inset + grip)
                fillet(
                    sk.vertices().sort_by_distance(pos)[0],
                    radius=max(
                        self.corner_radius - inset, self.corner_radius / 4
                    ),
                )
                if self.round_corners:
                    for sort_by_ref in (
                        (self.size, inset),
                        (inset, self.size),
                    ):
                        fillet(
                            sk.vertices().sort_by_distance(sort_by_ref)[:2],
                            radius=misc_radius * 2,
                        )
                    if self.edge_guides:
                        for sort_by_ref in (
                            (corner_space, grip),
                            (grip, corner_space),
                        ):
                            fillet(
                                sk.vertices().sort_by_distance(sort_by_ref)[
                                    :2
                                ],
                                radius=misc_radius * 0.99,
                            )
                if self.cutout_type == CutoutType.SQUARE:
                    with Locations((grip, grip)):
                        with (
                            Locations(
                                (
                                    corner_space
                                    + (self.size - corner_space) / 2
                                    - misc_spacing,
                                    inset / 2,
                                )
                            ),
                            GridLocations(
                                inset / 2 + misc_spacing,
                                inset,
                                floor(
                                    (
                                        self.size
                                        - corner_space
                                        - misc_spacing * 2
                                    )
                                    / (inset / 2 + misc_spacing)
                                ),
                                1,
                            ),
                        ):
                            RectangleRounded(
                                inset / 2,
                                inset / 2,
                                misc_spacing,
                                mode=Mode.SUBTRACT,
                            )
                        with (
                            Locations(
                                (
                                    inset / 2,
                                    corner_space
                                    + (self.size - corner_space) / 2
                                    - misc_spacing,
                                )
                            ),
                            GridLocations(
                                inset,
                                inset / 2 + misc_spacing,
                                1,
                                floor(
                                    (
                                        self.size
                                        - corner_space
                                        - misc_spacing * 2
                                    )
                                    / (inset / 2 + misc_spacing)
                                ),
                            ),
                        ):
                            RectangleRounded(
                                inset / 2,
                                inset / 2,
                                misc_spacing or (inset / 8),
                                mode=Mode.SUBTRACT,
                            )
                elif self.cutout_type == CutoutType.HATCH:
                    with Locations((grip, grip + 0)):
                        with (
                            Locations(
                                (
                                    corner_space
                                    + (self.size - corner_space) / 2
                                    - misc_spacing,
                                    inset / 2,
                                )
                            ),
                        ):
                            HatchPattern(
                                self.size - corner_space - inset / 2,
                                inset / 2,
                                misc_spacing * 2,
                                hatch_rotation=45,
                                mode=Mode.SUBTRACT,
                            )
                        with (
                            Locations(
                                (
                                    inset / 2,
                                    corner_space
                                    + (self.size - corner_space) / 2
                                    - misc_spacing
                                    - misc_spacing,
                                )
                            ),
                        ):
                            HatchPattern(
                                inset / 2,
                                self.size - corner_space - inset / 2,
                                misc_spacing * 2,
                                hatch_rotation=135,
                                mode=Mode.SUBTRACT,
                            )

            extrude(amount=self.thickness)
            if self.edge_guides:
                grip_length = self.size - corner_space - misc_radius * 3
                with BuildSketch(Plane.XY.offset(self.thickness)):
                    with Locations((corner_space + misc_radius, 0)):
                        Rectangle(
                            grip_length, grip, align=(Align.MIN, Align.MIN)
                        )
                    with Locations((0, corner_space + misc_radius)):
                        Rectangle(
                            grip, grip_length, align=(Align.MIN, Align.MIN)
                        )

                extrude(amount=self.grip_height)
                last = p.edges(Select.LAST).filter_by(
                    lambda e: (
                        self.grip_height < e.center().Z and e.length < grip * 2
                    )
                )
                fillet(last, self.grip_height * 0.999)

        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Router Jig"
        p.part.color = Color(0xB0EB00)
        return Compound(children=[p.part])
