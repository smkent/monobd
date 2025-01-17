from __future__ import annotations

from enum import Enum, auto

from build123d import (
    IN,
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    CounterBoreHole,
    GridLocations,
    Hole,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Select,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
    mirror,
    validate_inputs,
)

from . import constants


class RackMountWhichHalf(Enum):
    LEFT = auto()
    RIGHT = auto()


class RackFrame(Compound):
    def __init__(self, label: str = "frame") -> None:
        rm_left = RackFrameHalf(half=RackMountWhichHalf.LEFT)
        rm_left.color = Color(0xDDDDDD, alpha=0xFF)
        rm_right = RackFrameHalf(half=RackMountWhichHalf.RIGHT)
        rm_right.color = Color(0xDDDDDD, alpha=0xFF)
        super().__init__(  # type: ignore
            label=label, children=[rm_left, rm_right]
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
            all_u = [(0, uu * constants.U) for uu in range(0, u)]
            per_u = [(0, y) for y in (0, 5 / 8 * IN, -5 / 8 * IN)]
            with BuildSketch() as sk, Locations(*all_u), Locations(*per_u):
                RectangleRounded(2 / 5 * IN, 1 / 4 * IN, radius=(7 / 64 * IN))
            extrude(sk.sketch, amount=hole_depth)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RackFrameHalf(BasePartObject):
    def __init__(
        self,
        half: RackMountWhichHalf = RackMountWhichHalf.LEFT,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        outer_height = 1 * constants.U - constants.FIT * 2
        shift_direction = -1 if (half == RackMountWhichHalf.LEFT) else 1
        part_width = 19 / 2 * IN
        part_shift = shift_direction * (part_width - (17 + 1 / 4) / 2 * IN) / 2
        with BuildPart() as p:
            with BuildPart(mode=Mode.PRIVATE) as face_plate:
                with BuildSketch() as sk0:
                    Rectangle(part_width, outer_height)
                front_plate = extrude(
                    sk0.sketch, amount=constants.FACE_THICKNESS
                )
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
                    Locations((-part_shift, 0, constants.THICKNESS * 2)),
                ):
                    Rectangle(back_width, outer_height)
                with (
                    BuildSketch(
                        sk.faces()[0].offset(constants.THICKNESS * 10)
                    ) as sk2,
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
                    constants.TRAY_WIDTH
                    - constants.TRAY_EAR_WIDTH * 2
                    + constants.FIT,
                    constants.TRAY_HEIGHT + constants.FIT,
                    radius=1 / 8 * IN + constants.FIT,
                )
            tray_cutout = extrude(
                sk.sketch,
                amount=constants.FACE_THICKNESS + constants.THICKNESS * 10,
                mode=Mode.SUBTRACT,
            )
            chamfer(p.edges(Select.LAST).group_by(Axis.Z)[:], 1)

            if half == RackMountWhichHalf.LEFT:
                ff = tray_cutout.faces().group_by(Axis.X)[-1]
                with (
                    Locations(ff),
                    GridLocations(
                        5 / 16 * constants.U, constants.THICKNESS * 4, 2, 2
                    ),
                ):
                    hh = CounterBoreHole(
                        radius=constants.SCREW_HOLE_DIAMETER / 2,
                        counter_bore_radius=constants.SCREW_DIAMETER,
                        counter_bore_depth=constants.SCREW_DIAMETER * 1.25,
                        depth=part_width / 2,
                        mode=Mode.PRIVATE,
                    )
                    mirror(hh, about=Plane(ff[0]), mode=Mode.SUBTRACT)
            elif half == RackMountWhichHalf.RIGHT:
                ff = tray_cutout.faces().group_by(Axis.X)[0]
                with (
                    Locations(ff),
                    GridLocations(
                        5 / 16 * constants.U, constants.THICKNESS * 4, 2, 2
                    ),
                ):
                    hh = Hole(
                        radius=constants.SCREW_INSERT_DIAMETER / 2,
                        depth=part_width / 2,
                        mode=Mode.PRIVATE,
                    )
                    mirror(hh, about=Plane(ff[0]), mode=Mode.SUBTRACT)
                    chamfer(p.edges(Select.LAST).group_by(Axis.X)[:], 1)

            # Tray screw holes
            with GridLocations(
                constants.TRAY_FACE_SCREW_HORIZONTAL_SPACING,
                constants.TRAY_FACE_SCREW_VERTICAL_SPACING,
                2,
                2,
            ):
                Hole(
                    radius=constants.SCREW_INSERT_DIAMETER / 2,
                    mode=Mode.SUBTRACT,
                )
                chamfer(p.edges(Select.LAST).group_by(Axis.Z)[:], 1)

        p.part.label = f"half-{half.name.lower()}"
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
