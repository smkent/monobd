from __future__ import annotations

from enum import Enum, auto
from math import floor

from bdbox import Model, Preset
from build123d import (
    IN,
    MM,
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
    size_in: float = 8
    corner_radius_in: float = 1
    corner_space_in: float = 2
    thickness_mm: float = 5
    span_in: float = 2.5
    grip_in: float = 0.25
    grip_height_in: float = 0.75
    round_corners: bool = True
    edge_guides: bool = True
    cutout_type: CutoutType = CutoutType.HATCH

    presets = (
        Preset(
            "1 inch",
            size_in=8,
            corner_radius_in=1,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
        Preset(
            "2 inch",
            size_in=9,
            corner_radius_in=2,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
        Preset(
            "3 inch",
            size_in=10,
            corner_radius_in=3,
            round_corners=True,
            edge_guides=True,
            cutout_type=CutoutType.HATCH,
        ),
    )

    def build(self) -> Model.Build:
        size = self.size_in * IN
        corner_radius = self.corner_radius_in * IN
        corner_space = self.corner_space_in * IN + corner_radius
        thickness = self.thickness_mm * MM
        inset = self.span_in * IN
        grip = self.grip_in * IN if self.edge_guides else 0
        misc_spacing = max(1 / 8 * IN, self.grip_in * IN or (inset / 8))
        misc_radius = misc_spacing / 2 if self.round_corners else 0
        with BuildPart() as p:
            with BuildSketch() as sk:
                L(size, inset + grip, align=(Align.MIN, Align.MIN))
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
                    radius=corner_radius,
                )
                pos = (inset + grip, inset + grip)
                fillet(
                    sk.vertices().sort_by_distance(pos)[0],
                    radius=max(corner_radius - inset, corner_radius / 4),
                )
                if self.round_corners:
                    for sort_by_ref in ((size, inset), (inset, size)):
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
                                    + (size - corner_space) / 2
                                    - misc_spacing,
                                    inset / 2,
                                )
                            ),
                            GridLocations(
                                inset / 2 + misc_spacing,
                                inset,
                                floor(
                                    (size - corner_space - misc_spacing * 2)
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
                                    + (size - corner_space) / 2
                                    - misc_spacing,
                                )
                            ),
                            GridLocations(
                                inset,
                                inset / 2 + misc_spacing,
                                1,
                                floor(
                                    (size - corner_space - misc_spacing * 2)
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
                                    + (size - corner_space) / 2
                                    - misc_spacing,
                                    inset / 2,
                                )
                            ),
                        ):
                            HatchPattern(
                                size - corner_space - inset / 2,
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
                                    + (size - corner_space) / 2
                                    - misc_spacing
                                    - misc_spacing,
                                )
                            ),
                        ):
                            HatchPattern(
                                inset / 2,
                                size - corner_space - inset / 2,
                                misc_spacing * 2,
                                hatch_rotation=135,
                                mode=Mode.SUBTRACT,
                            )

            extrude(amount=thickness)
            if self.edge_guides:
                grip_length = size - corner_space - misc_radius * 3
                with BuildSketch(Plane.XY.offset(thickness)):
                    with Locations((corner_space + misc_radius, 0)):
                        Rectangle(
                            grip_length, grip, align=(Align.MIN, Align.MIN)
                        )
                    with Locations((0, corner_space + misc_radius)):
                        Rectangle(
                            grip, grip_length, align=(Align.MIN, Align.MIN)
                        )

                extrude(amount=self.grip_height_in * IN)
                last = p.edges(Select.LAST).filter_by(
                    lambda e: (
                        self.grip_height_in * IN < e.center().Z
                        and e.length < grip * 2
                    )
                )
                fillet(
                    last,
                    self.grip_height_in * IN * 0.999,
                )

        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Router Jig"
        p.part.color = Color(0xB0EB00)
        return Compound(children=[p.part])
