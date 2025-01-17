from __future__ import annotations

from pathlib import Path

from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    GridLocations,
    Hole,
    Locations,
    Mode,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Select,
    SortBy,
    chamfer,
    extrude,
)

from ...objects import HexagonPattern, PrintableCounterBoreHole, SVGSketch
from . import constants


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
                    constants.TRAY_WIDTH,
                    constants.TRAY_FACE_HEIGHT,
                    radius=(1 / 8) * IN,
                )
                RectangleRounded(
                    *cutout_size, radius=(1 / 8) * IN, mode=Mode.SUBTRACT
                )
                with GridLocations(
                    constants.TRAY_FACE_SCREW_HORIZONTAL_SPACING,
                    constants.TRAY_FACE_SCREW_VERTICAL_SPACING,
                    2,
                    2,
                ):
                    Circle(
                        radius=constants.SCREW_HOLE_DIAMETER / 2,
                        mode=Mode.SUBTRACT,
                    )
            extrude(sk.sketch, amount=constants.THICKNESS)
            for face_index in [-1, 0]:
                for distance_index in [-1, 0]:
                    chamfer(
                        p.edges()
                        .group_by(Axis.Z)[face_index]
                        .sort_by(SortBy.DISTANCE)[distance_index],
                        length=constants.THICKNESS / 4,
                    )
            if image_file:
                image_space = min(
                    constants.TRAY_FACE_HEIGHT,
                    (constants.TRAY_WIDTH - cutout_size[0]) / 2 - 1 / 2 * IN,
                )
                with Locations(
                    (-(constants.TRAY_WIDTH + cutout_size[0]) / 4, 0, 0)
                ):
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
        depth = self.dev_depth + constants.LIP + (1 * MM)
        with BuildPart() as p:
            with BuildSketch() as sk:
                RectangleRounded(
                    self.dev_width
                    + constants.WALL_THICKNESS * 2
                    + constants.SCREW_SUPPORT_DIAMETER * 2,
                    min(
                        constants.TRAY_HEIGHT,
                        self.dev_height + constants.WALL_THICKNESS * 2,
                    ),
                    radius=(1 / 8) * IN,
                )
            body = extrude(sk.sketch, amount=depth)

            # Screw holes
            with (
                Locations(body.faces().sort_by(Axis.Z)[-1]),
                GridLocations(
                    self.dev_width
                    + constants.WALL_THICKNESS
                    + constants.SCREW_SUPPORT_DIAMETER,
                    self.dev_height
                    + constants.WALL_THICKNESS * 2
                    - constants.SCREW_SUPPORT_DIAMETER * 2,
                    2,
                    2,
                ),
            ):
                Hole(
                    radius=constants.SCREW_INSERT_DIAMETER / 2,
                    depth=5 / 16 * IN,
                )
            chamfer(p.edges(Select.LAST).group_by(Axis.Z)[-1], length=1)

            # Hex pattern
            if hexagon_pattern:
                for yf in [body.faces().sort_by(Axis.Y)[i] for i in (-1, 0)]:
                    with BuildSketch(yf) as sk:
                        HexagonPattern(
                            self.dev_width - constants.WALL_THICKNESS * 2,
                            depth - constants.THICKNESS * 2,
                            whole_only=True,
                            align=(Align.CENTER, Align.CENTER),
                            mode=Mode.ADD,
                        )
                    extrude(
                        sk.sketch,
                        amount=-constants.WALL_THICKNESS,
                        mode=Mode.SUBTRACT,
                    )
                for yf in [body.faces().sort_by(Axis.X)[i] for i in (-1, 0)]:
                    with BuildSketch(yf) as sk:
                        HexagonPattern(
                            self.dev_height - constants.WALL_THICKNESS * 1,
                            depth
                            - constants.THICKNESS * 2
                            - constants.SCREW_SUPPORT_DIAMETER * 2,
                            whole_only=False,
                            hex_size=6,
                            align=(Align.CENTER, Align.CENTER),
                            mode=Mode.ADD,
                        )
                    extrude(
                        sk.sketch,
                        amount=-(
                            constants.WALL_THICKNESS
                            + constants.SCREW_SUPPORT_DIAMETER
                        ),
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
                    + constants.WALL_THICKNESS * 2
                    + constants.SCREW_SUPPORT_DIAMETER * 2,
                    min(
                        constants.TRAY_HEIGHT,
                        self.dev_height + constants.WALL_THICKNESS * 2,
                    ),
                    radius=(1 / 8) * IN,
                )
            back = extrude(sk.sketch, amount=constants.THICKNESS)
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[-1], length=1)
            with BuildSketch(back.faces().sort_by(Axis.Z)[0]) as sk:
                RectangleRounded(
                    self.dev_width - constants.FIT,
                    min(constants.TRAY_HEIGHT, self.dev_height)
                    - constants.FIT,
                    radius=(1 / 8) * IN,
                )
            extrude(sk.sketch, amount=constants.LIP)
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[0], length=0.6 * MM)
            with BuildSketch(back.faces().sort_by(Axis.Z)[-1]) as sk:
                RectangleRounded(*cutout_size, radius=(1 / 8) * IN)
            extrude(
                sk.sketch,
                amount=-(constants.THICKNESS + constants.LIP),
                mode=Mode.SUBTRACT,
            )
            chamfer(p.edges(Select.LAST).sort_by(Axis.Z)[:], length=0.6 * MM)
            with (
                Locations(back.faces().sort_by(Axis.Z)[-1]),
                GridLocations(
                    self.dev_width
                    + constants.WALL_THICKNESS
                    + constants.SCREW_SUPPORT_DIAMETER,
                    self.dev_height
                    + constants.WALL_THICKNESS * 2
                    - constants.SCREW_SUPPORT_DIAMETER * 2,
                    2,
                    2,
                ),
            ):
                PrintableCounterBoreHole(
                    radius=constants.SCREW_HOLE_DIAMETER / 2,
                    counter_bore_radius=constants.SCREW_DIAMETER,
                    counter_bore_depth=min(
                        constants.SCREW_DIAMETER * 1.25,
                        constants.THICKNESS / 2,
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
        label: str = "trays",
        hexagon_pattern: bool = True,
    ):
        if cutout_size is None:
            cutout_size = (
                device_size[0] - 1 / 4 * IN,
                device_size[1] - 1 / 4 * IN,
            )
        device_size = tuple(
            v + constants.FIT for v in device_size
        )  # type: ignore
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
                amount=self.dev_depth + 1 * MM + constants.LIP,
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
            Locations((0, 0, constants.THICKNESS)),
        ):
            RackTrayBack(
                device_size,
                cutout_size,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )
        back.part.label = "back"
        super().__init__(  # type: ignore
            label=label, children=[body.part, back.part]
        )
