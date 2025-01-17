from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from pathlib import Path
from typing import Any

from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    CounterBoreHole,
    GridLocations,
    Hole,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Select,
    SortBy,
    add,
    chamfer,
    extrude,
    fillet,
    import_svg,
    loft,
    mirror,
    scale,
    validate_inputs,
)

from ..assets import asset
from ..common import Model
from ..objects import HexagonPattern

FIT = 0.2 * MM
LIP = 1.6 * MM
U = (1 + 3 / 4) * IN
SCREW_DIAMETER = 3 * MM
SCREW_HOLE_DIAMETER = SCREW_DIAMETER + FIT
SCREW_INSERT_DIAMETER = 4.5 * MM
SCREW_SUPPORT_DIAMETER = 1 / 4 * IN
TRAY_WIDTH = 8.25 * IN
TRAY_HEIGHT = 1 * U - (1 / 2 * IN)
TRAY_FACE_SCREW_HORIZONTAL_SPACING = TRAY_WIDTH - (1 / 2) * IN
TRAY_FACE_SCREW_VERTICAL_SPACING = TRAY_HEIGHT - (1 / 4) * IN
TRAY_FACE_HEIGHT = 1 * U - (1 / 8 * IN)
TRAY_EAR_WIDTH = 1 / 2 * IN
THICKNESS = 1 / 8 * IN
FACE_THICKNESS = 1 / 4 * IN
WALL_THICKNESS = 2.4 * MM
TRAY_LOCATIONS = ((-(17 + 1 / 4) / 4 * IN, 0), ((17 + 1 / 4) / 4 * IN, 0))


class RackMountWhichHalf(Enum):
    LEFT = auto()
    RIGHT = auto()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self.name}>"


class SVGSketch(BaseSketchObject):
    def __init__(
        self,
        file_name: str | Path,
        size: float,
        rotation: float = 180,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        with BuildSketch() as sk:
            ep = import_svg(str(file_name))
            ep = mirror(ep, about=Plane.YZ)
            max_dim = max(ep.bounding_box().size.Y, ep.bounding_box().size.X)
            ep = scale(ep, by=(size / max_dim))
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class PrintableCounterBoreHole(BasePartObject):
    def __init__(
        self,
        radius: float,
        counter_bore_radius: float,
        counter_bore_depth: float,
        depth: float | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
    ):
        context: BuildPart = BuildPart._get_context(self)
        validate_inputs(context, self)
        if depth is None:
            depth = context.max_dimension
        with BuildPart() as p:
            CounterBoreHole(
                radius=radius,
                counter_bore_radius=counter_bore_radius,
                counter_bore_depth=counter_bore_depth,
                depth=depth,
                mode=Mode.ADD,
            )
            with BuildSketch(p.faces().sort_by(Axis.Z)[2]) as sk:
                Circle(radius=counter_bore_radius)
                Rectangle(
                    counter_bore_radius,
                    counter_bore_radius * 2,
                    mode=Mode.SUBTRACT,
                )
            extrude(sk.sketch, amount=-0.4, mode=Mode.SUBTRACT)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackHoles(BasePartObject):
    def __init__(
        self,
        u: int = 1,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
        depth: float | None = None,
    ):
        context: BuildPart = BuildPart._get_context(self)
        validate_inputs(context, self)
        hole_depth = depth * 2 if depth is not None else context.max_dimension
        with BuildPart() as p:
            all_u = [(0, uu * U) for uu in range(0, u)]
            per_u = [(0, y) for y in (0, 5 / 8 * IN, -5 / 8 * IN)]
            with BuildSketch() as sk, Locations(*all_u), Locations(*per_u):
                RectangleRounded(2 / 5 * IN, 1 / 4 * IN, radius=(7 / 64 * IN))
            extrude(sk.sketch, amount=hole_depth)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackTrayFront(BasePartObject):
    def __init__(
        self,
        device_size: tuple[float, float, float],
        cutout_size: tuple[float, float],
        image_file: Path | str = "",
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        self.dev_width, self.dev_height, self.dev_depth = device_size
        with BuildPart() as p:
            with BuildSketch() as sk:
                RectangleRounded(
                    TRAY_WIDTH,
                    TRAY_FACE_HEIGHT,
                    radius=(1 / 8) * IN,
                )
                RectangleRounded(
                    *cutout_size, radius=(1 / 8) * IN, mode=Mode.SUBTRACT
                )
                with GridLocations(
                    TRAY_FACE_SCREW_HORIZONTAL_SPACING,
                    TRAY_FACE_SCREW_VERTICAL_SPACING,
                    2,
                    2,
                ):
                    Circle(radius=SCREW_HOLE_DIAMETER / 2, mode=Mode.SUBTRACT)
            extrude(sk.sketch, amount=THICKNESS)
            for face_index in [-1, 0]:
                for distance_index in [-1, 0]:
                    chamfer(
                        p.edges()
                        .group_by(Axis.Z)[face_index]
                        .sort_by(SortBy.DISTANCE)[distance_index],
                        length=THICKNESS / 4,
                    )
            if image_file:
                image_space = min(
                    TRAY_FACE_HEIGHT,
                    (TRAY_WIDTH - cutout_size[0]) / 2 - 1 / 2 * IN,
                )
                with Locations((-(TRAY_WIDTH + cutout_size[0]) / 4, 0, 0)):
                    sp = SVGSketch(file_name=image_file, size=image_space)
                extrude(sp, amount=0.8, mode=Mode.SUBTRACT)

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackTrayBody(BasePartObject):
    def __init__(
        self,
        device_size: tuple[float, float, float] = (0, 0, 0),
        hexagon_pattern: bool = True,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        self.dev_width, self.dev_height, self.dev_depth = device_size
        depth = self.dev_depth + LIP + (1 * MM)
        with BuildPart() as p:
            with BuildSketch() as sk:
                RectangleRounded(
                    self.dev_width
                    + WALL_THICKNESS * 2
                    + SCREW_SUPPORT_DIAMETER * 2,
                    min(TRAY_HEIGHT, self.dev_height + WALL_THICKNESS * 2),
                    radius=(1 / 8) * IN,
                )
            body = extrude(sk.sketch, amount=depth)

            # Screw holes
            with (
                Locations(body.faces().sort_by(Axis.Z)[-1]),
                GridLocations(
                    self.dev_width + WALL_THICKNESS + SCREW_SUPPORT_DIAMETER,
                    self.dev_height
                    + WALL_THICKNESS * 2
                    - SCREW_SUPPORT_DIAMETER * 2,
                    2,
                    2,
                ),
            ):
                Hole(radius=SCREW_INSERT_DIAMETER / 2, depth=5 / 16 * IN)
            chamfer(p.edges(Select.LAST).group_by(Axis.Z)[-1], length=1)

            # Hex pattern
            if hexagon_pattern:
                for yf in [body.faces().sort_by(Axis.Y)[i] for i in (-1, 0)]:
                    with BuildSketch(yf) as sk:
                        HexagonPattern(
                            self.dev_width - WALL_THICKNESS * 2,
                            depth - THICKNESS * 2,
                            whole_only=True,
                            align=(Align.CENTER, Align.CENTER),
                            mode=Mode.ADD,
                        )
                    extrude(
                        sk.sketch, amount=-WALL_THICKNESS, mode=Mode.SUBTRACT
                    )
                for yf in [body.faces().sort_by(Axis.X)[i] for i in (-1, 0)]:
                    with BuildSketch(yf) as sk:
                        HexagonPattern(
                            self.dev_height - WALL_THICKNESS * 1,
                            depth - THICKNESS * 2 - SCREW_SUPPORT_DIAMETER * 2,
                            whole_only=False,
                            hex_size=6,
                            align=(Align.CENTER, Align.CENTER),
                            mode=Mode.ADD,
                        )
                    extrude(
                        sk.sketch,
                        amount=-(WALL_THICKNESS + SCREW_SUPPORT_DIAMETER),
                        mode=Mode.SUBTRACT,
                    )

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackTrayBack(BasePartObject):
    def __init__(
        self,
        device_size: tuple[float, float, float],
        cutout_size: tuple[float, float],
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        self.dev_width, self.dev_height, self.dev_depth = device_size
        with BuildPart() as p:
            with BuildSketch() as sk:
                RectangleRounded(
                    self.dev_width
                    + WALL_THICKNESS * 2
                    + SCREW_SUPPORT_DIAMETER * 2,
                    min(TRAY_HEIGHT, self.dev_height + WALL_THICKNESS * 2),
                    radius=(1 / 8) * IN,
                )
            back = extrude(sk.sketch, amount=THICKNESS)
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[-1], length=1)
            with BuildSketch(back.faces().sort_by(Axis.Z)[0]) as sk:
                RectangleRounded(
                    self.dev_width - FIT,
                    min(TRAY_HEIGHT, self.dev_height) - FIT,
                    radius=(1 / 8) * IN,
                )
            extrude(sk.sketch, amount=LIP)
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[0], length=0.6 * MM)
            with BuildSketch(back.faces().sort_by(Axis.Z)[-1]) as sk:
                RectangleRounded(*cutout_size, radius=(1 / 8) * IN)
            extrude(sk.sketch, amount=-(THICKNESS + LIP), mode=Mode.SUBTRACT)
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[:], length=0.6 * MM)
            with (
                Locations(back.faces().sort_by(Axis.Z)[-1]),
                GridLocations(
                    self.dev_width + WALL_THICKNESS + SCREW_SUPPORT_DIAMETER,
                    self.dev_height
                    + WALL_THICKNESS * 2
                    - SCREW_SUPPORT_DIAMETER * 2,
                    2,
                    2,
                ),
            ):
                PrintableCounterBoreHole(
                    radius=SCREW_HOLE_DIAMETER / 2,
                    counter_bore_radius=SCREW_DIAMETER,
                    counter_bore_depth=min(
                        SCREW_DIAMETER * 1.25, THICKNESS / 2
                    ),
                    mode=Mode.SUBTRACT,
                )
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackTray(Compound):
    def __init__(
        self,
        device_size: tuple[float, float, float],
        cutout_size: tuple[float, float] | None = None,
        image_file: Path | str = "",
        label: str = "rack-tray",
        hexagon_pattern: bool = True,
    ):
        if cutout_size is None:
            cutout_size = (
                device_size[0] - 1 / 4 * IN,
                device_size[1] - 1 / 4 * IN,
            )
        device_size = tuple(v + FIT for v in device_size)  # type: ignore
        self.dev_width, self.dev_height, self.dev_depth = device_size
        with BuildPart() as body:
            # Front face
            front = RackTrayFront(
                device_size,
                cutout_size,
                image_file=image_file,
            )
            # Add body
            face = front.faces().group_by(Axis.Z)[-1]
            with Locations(face):
                RackTrayBody(device_size, hexagon_pattern=hexagon_pattern)
            chamfer(body.edges(Select.LAST).group_by(Axis.Z)[0], 1 * MM)
            # Cut out interior
            with BuildSketch(face) as sk:
                Rectangle(self.dev_width, self.dev_height)
            extrude(
                sk.sketch,
                amount=self.dev_depth + 1 * MM + LIP,
                mode=Mode.SUBTRACT,
            )
            # Chamfer tray interior
            cutout_edges = body.edges(Select.LAST).group_by(Axis.Z)
            chamfer(cutout_edges[0], length=1 * MM)
            chamfer(cutout_edges[-1], length=0.4 * MM)
        body.part.label = "body"
        with (
            BuildPart() as back,
            Locations(body.faces().group_by(Axis.Z)[-1]),
            Locations((0, 0, THICKNESS)),
        ):
            RackTrayBack(
                device_size,
                cutout_size,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )
        back.part.label = "back"
        super().__init__(  # type: ignore
            label=f"{label}", children=[body.part, back.part]
        )


class RackMountHalf(BasePartObject):
    def __init__(
        self,
        half: RackMountWhichHalf = RackMountWhichHalf.LEFT,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.SUBTRACT,
        depth: float | None = None,
    ):
        outer_height = 1 * U - FIT * 2
        shift_direction = -1 if (half == RackMountWhichHalf.LEFT) else 1
        part_width = 19 / 2 * IN
        part_shift = shift_direction * (part_width - (17 + 1 / 4) / 2 * IN) / 2
        with BuildPart() as p:
            with BuildPart(mode=Mode.PRIVATE) as face_plate:
                with BuildSketch() as sk0:
                    Rectangle(part_width, outer_height)
                front_plate = extrude(sk0.sketch, amount=FACE_THICKNESS)
                fillet(
                    face_plate.edges(Select.LAST)
                    .group_by(Axis.Z)[1]
                    .group_by(Axis.X)[
                        0 if half == RackMountWhichHalf.LEFT else -1
                    ],
                    radius=1 / 8 * IN,
                )
                chamfer(face_plate.edges(Select.LAST).group_by(Axis.Z)[0], 1)
                front_plate_back_face = front_plate.faces().group_by(Axis.Z)[
                    -1
                ]
                holes_inset = part_width - (18 + 5 / 16) / 2 * IN
                with Locations(
                    (shift_direction * (part_width / 2 - holes_inset), 0, 0)
                ):
                    RackHoles(mode=Mode.SUBTRACT)
                chamfer(face_plate.edges(Select.LAST).group_by(Axis.Z)[:], 0.4)

                back_width = part_width - abs(part_shift * 2)
                with (
                    BuildSketch(front_plate_back_face) as sk,
                    Locations((-part_shift, 0, THICKNESS * 2)),
                ):
                    Rectangle(back_width, outer_height)
                with (
                    BuildSketch(sk.faces()[0].offset(THICKNESS * 10)) as sk2,
                    Locations((-shift_direction * back_width / 2, 0)),
                ):
                    Rectangle(
                        (2 + 5 / 8) * IN,
                        outer_height,
                        align=(
                            (
                                Align.MAX
                                if half == RackMountWhichHalf.LEFT
                                else Align.MIN
                            ),
                            Align.CENTER,
                        ),
                    )
                ll = loft([sk.sketch, sk2.sketch])
                fillet(ll.edges().group_by(Axis.Z)[-1], 10 * IN)
                fillet(ll.edges().group_by(Axis.Z)[0], 0.25 * IN)
                chamfer(
                    face_plate.edges()
                    .group_by(Axis.X)[
                        0 if half == RackMountWhichHalf.LEFT else -1
                    ]
                    .group_by(Axis.Z)[2],
                    1,
                )

            with Locations((part_shift, 0, 0)):
                add(face_plate)

            # Tray cutout
            with BuildSketch() as sk:
                RectangleRounded(
                    TRAY_WIDTH - TRAY_EAR_WIDTH * 2 + FIT,
                    TRAY_HEIGHT + FIT,
                    radius=1 / 8 * IN + FIT,
                )
            tray_cutout = extrude(
                sk.sketch,
                amount=FACE_THICKNESS + THICKNESS * 10,
                mode=Mode.SUBTRACT,
            )
            chamfer(p.edges(Select.LAST).group_by(Axis.Z)[:], 1)

            if half == RackMountWhichHalf.LEFT:
                ff = tray_cutout.faces().group_by(Axis.X)[-1]
                with (
                    Locations(ff),
                    GridLocations(5 / 16 * U, THICKNESS * 4, 2, 2),
                ):
                    hh = CounterBoreHole(
                        radius=SCREW_HOLE_DIAMETER / 2,
                        counter_bore_radius=SCREW_DIAMETER,
                        counter_bore_depth=SCREW_DIAMETER * 1.25,
                        depth=part_width / 2,
                        mode=Mode.PRIVATE,
                    )
                    mirror(hh, about=Plane(ff[0]), mode=Mode.SUBTRACT)
            elif half == RackMountWhichHalf.RIGHT:
                ff = tray_cutout.faces().group_by(Axis.X)[0]
                with (
                    Locations(ff),
                    GridLocations(5 / 16 * U, THICKNESS * 4, 2, 2),
                ):
                    hh = Hole(
                        radius=SCREW_INSERT_DIAMETER / 2,
                        depth=part_width / 2,
                        mode=Mode.PRIVATE,
                    )
                    mirror(hh, about=Plane(ff[0]), mode=Mode.SUBTRACT)
                    chamfer(p.edges(Select.LAST).group_by(Axis.X)[:], 1)

            # Tray screw holes
            with GridLocations(
                TRAY_FACE_SCREW_HORIZONTAL_SPACING,
                TRAY_FACE_SCREW_VERTICAL_SPACING,
                2,
                2,
            ):
                Hole(radius=SCREW_INSERT_DIAMETER / 2, mode=Mode.SUBTRACT)
                chamfer(p.edges(Select.LAST).group_by(Axis.Z)[:], 1)

        super().__init__(
            part=p.part,
            rotation=rotation,
            align=(
                (
                    (
                        Align.MAX
                        if half == RackMountWhichHalf.LEFT
                        else Align.MIN
                    ),
                    Align.CENTER,
                    Align.MIN,
                )
                if align is None
                else align
            ),
            mode=mode,
        )


@dataclass
class AVRack(Model, name="avrack"):
    simple: bool = False

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {"default": {}, "simple": {"simple": True}}

    @cached_property
    def assembly(self) -> Compound:
        rm_left = RackMountHalf(half=RackMountWhichHalf.LEFT)
        rm_left.label = "rack-mount-left"
        rm_right = RackMountHalf(half=RackMountWhichHalf.RIGHT)
        rm_right.label = "rack-mount-right"
        rt = RackTray(
            device_size=((6 + 5 / 16) * IN, (1 + 1 / 32) * IN, 4 * IN),
            cutout_size=((5 + 3 / 4) * IN, 13 / 16 * IN),
            image_file=asset("ethernet-port.svg"),
            label="ethernet-switch",
            hexagon_pattern=not self.simple,
        )
        rt = rt.move(Location(TRAY_LOCATIONS[0]))
        rt = rt.move(Location((0, 0, -THICKNESS)))
        rt2 = RackTray(
            device_size=(5 * IN, (1 + 1 / 32) * IN, 5 * IN),
            cutout_size=((3 + 1 / 2) * IN, (3 / 4) * IN),
            image_file=asset("roku-logo.svg"),
            label="roku",
            hexagon_pattern=not self.simple,
        )
        rt2 = rt2.move(Location(TRAY_LOCATIONS[1]))
        rt2 = rt2.move(Location((0, 0, -THICKNESS)))
        rt3 = RackTray(
            device_size=(
                (6 + 1 / 2 - 1 / 32) * IN,
                (3 / 4) * IN,
                (2 + 1 / 2) * IN,
            ),
            cutout_size=(6 * IN, (19 / 32) * IN),
            image_file=asset("hdmi-port.svg"),
            label="hdmi-duplicator",
            hexagon_pattern=not self.simple,
        )
        rt3 = rt3.move(Location((0, 1 * U, -THICKNESS)))
        trays = Compound(  # type: ignore
            label="trays", children=[rt, rt2, rt3]
        )
        return Compound(  # type: ignore
            label=self.model_name, children=[rm_left, rm_right, trays]
        )
