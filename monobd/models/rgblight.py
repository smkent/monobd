from __future__ import annotations

from bd_warehouse.thread import Thread
from bdbox import Model
from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    GridLocations,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RotationLike,
    Select,
    chamfer,
    extrude,
    fillet,
)


class Const:
    diameter: float = 2.5 * IN
    base_height = 1 * IN
    thickness: float = 1.6 * MM
    led_mount_diameter = 0.5 * IN
    led_mount_height = 2 * IN

    thread_inset = 0.5 * IN
    thread_height = 0.25 * IN
    thread_clearance = 0.6 * MM  # 0.25 * MM
    thread_pitch = 6 * MM


class BodyHalf(BasePartObject):
    def __init__(
        self,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            Cylinder(
                Const.diameter / 2,
                height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            fillet(
                p.edges(Select.LAST).group_by(Axis.Z)[-1],
                Const.base_height / 3,
            )

            with BuildPart(mode=Mode.SUBTRACT) as p2_sub:
                with Locations((0, 0, Const.thread_height)):
                    Cylinder(
                        Const.diameter / 2 - Const.thickness,
                        height - Const.thread_height - Const.thickness * 1,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                last_edges = p2_sub.edges(Select.LAST)
                fillet(
                    last_edges.group_by(Axis.Z)[-1],
                    Const.base_height / 3 - Const.thickness * 1,
                )
                chamfer(
                    last_edges.group_by(Axis.Z)[0],
                    Const.thread_inset / 2 / 2,
                )

            Cylinder(
                (
                    Const.diameter
                    - Const.thread_inset
                    + Const.thread_clearance
                    + 0.1
                )
                / 2,
                (Const.thread_height),
                mode=Mode.SUBTRACT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            Thread(
                apex_radius=(
                    Const.diameter
                    - Const.thread_inset / 2
                    + Const.thread_clearance
                )
                / 2,
                root_radius=(
                    Const.diameter
                    - Const.thread_inset
                    + Const.thread_clearance
                )
                / 2,
                apex_width=2 * MM + Const.thread_clearance,
                root_width=4 * MM + Const.thread_clearance,
                length=Const.thread_height * 2,
                end_finishes=("raw", "raw"),
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
                pitch=Const.thread_pitch,
            )

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class FixtureInsert(BasePartObject):
    def __init__(
        self,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            Cylinder(
                (Const.diameter - Const.thread_inset) / 2,
                Const.thread_height * 2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            Thread(
                apex_radius=(Const.diameter - Const.thread_inset / 2) / 2,
                root_radius=(Const.diameter - Const.thread_inset - 0.01) / 2,
                length=Const.thread_height * 2,
                apex_width=2 * MM,
                root_width=4 * MM,
                end_finishes=("chamfer", "chamfer"),
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.ADD,
                pitch=Const.thread_pitch,
            )

            with BuildSketch() as sk:
                Circle(
                    (Const.diameter - Const.thread_inset) / 2
                    - Const.thickness * 2
                )
                Circle(
                    (Const.led_mount_diameter) / 2 + Const.thickness,
                    mode=Mode.SUBTRACT,
                )
                Rectangle(
                    Const.diameter,
                    max(0.25 * IN, Const.led_mount_diameter / 2),
                    mode=Mode.SUBTRACT,
                )
                fillet(sk.vertices(), Const.thickness)
            extrude(amount=Const.thread_height * 2, mode=Mode.SUBTRACT)

            with Locations((0, 0, Const.thread_height)):
                Cylinder(
                    Const.led_mount_diameter / 2,
                    Const.led_mount_height - Const.thickness * 2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            chamfer(
                p.edges(Select.LAST).group_by(Axis.Z)[:],
                Const.thickness * 0.99,
            )

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class USBPortCutout(BasePartObject):
    def __init__(
        self,
        width: float = 15 * MM,
        height: float = 8 * MM,
        curve: float = 2 * MM,
        rotation: RotationLike = (90, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch(Plane.XY.offset(Const.diameter / 2)) as sk:
                Rectangle(width, height)
                fillet(sk.vertices(), curve)
            extrude(amount=-Const.thickness * 3)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RGBLight(Model):
    def build(self) -> Compound:
        with BuildPart() as fixture_base:
            BodyHalf(
                height=Const.base_height,
                rotation=(180, 0, 0),
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )

            # PCB mount
            with BuildPart():
                with BuildSketch() as sk:
                    Rectangle(Const.diameter * 2, Const.diameter * 2)
                    Rectangle(Const.diameter * 2, 20, mode=Mode.SUBTRACT)
                    Rectangle(20, Const.diameter * 2, mode=Mode.SUBTRACT)
                    fillet(sk.vertices(), 3 * MM)
                extrude(amount=10 * MM)
                with BuildSketch(), GridLocations(32 - 5, 32 - 5, 2, 2):
                    Circle(4.5 * MM / 2)
                extrude(amount=10 * MM, mode=Mode.SUBTRACT)
                with BuildPart(mode=Mode.INTERSECT) as p_int:
                    Cylinder(
                        Const.diameter / 2,
                        Const.base_height,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                    fillet(
                        p_int.edges(Select.LAST).group_by(Axis.Z)[0],
                        Const.base_height / 3,
                    )
            chamfer(fixture_base.edges(Select.LAST).group_by(Axis.Z)[:], 0.6)

            # USB port
            with Locations(
                (
                    0,
                    Const.diameter / 2,
                    Const.thickness + 10 * MM + -(1 + 2.5) * MM,
                )
            ):
                USBPortCutout(
                    mode=Mode.SUBTRACT,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            # Ambient light sensor
            with Locations(
                (
                    0,
                    -Const.diameter / 2,
                    Const.thickness + 10 * MM + (1.6 + 1.5) * MM,
                )
            ):
                USBPortCutout(
                    8,
                    4,
                    1,
                    mode=Mode.SUBTRACT,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )

        fixture_base.part.label = "base"
        fixture_base.part.color = Color(0x11AACC, alpha=0xCC)

        with BuildPart() as fixture_insert:
            FixtureInsert()
        fixture_insert.part.label = "insert"
        fixture_insert.part.color = Color(0x11CC88, alpha=0xCC)
        fixture_insert.part = fixture_insert.part.move(
            Location((0, 0, Const.base_height - Const.thread_height))
        )

        with BuildPart() as fixture_diffuser:
            BodyHalf(height=Const.led_mount_height)
        fixture_diffuser.part.label = "diffuser"
        fixture_diffuser.part.color = Color(0xDDDDDD, alpha=0xCC)
        fixture_diffuser.part = fixture_diffuser.part.move(
            Location((0, 0, Const.base_height))
        )

        return Compound(
            children=[
                fixture_base.part,
                fixture_insert.part,
                fixture_diffuser.part,
            ],
        )
