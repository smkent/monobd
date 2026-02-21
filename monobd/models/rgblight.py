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
    Location,
    Locations,
    Mode,
    Rectangle,
    RotationLike,
    Select,
    chamfer,
    extrude,
    fillet,
)


class Const:
    diameter: float = 2 * IN
    base_height = 1 * IN
    led_mount_diameter = 0.5 * IN
    led_mount_height = 2 * IN

    thread_inset = 0.5 * IN
    thread_height = 0.25 * IN
    thread_clearance = 2  # 0.25 * MM

    thickness: float = 1.6 * MM

    thread_args = {  # noqa: RUF012
        "apex_width": 2,
        "root_width": 4,
        "pitch": 8,
        "end_finishes": ["chamfer", "chamfer"],
        "align": (Align.CENTER, Align.CENTER, Align.MIN),
    }


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
                fillet(
                    p2_sub.edges(Select.LAST).group_by(Axis.Z)[-1],
                    Const.base_height / 3 - Const.thickness * 1,
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
                apex_radius=(Const.diameter - Const.thread_inset / 2) / 2,
                root_radius=(
                    Const.diameter
                    - Const.thread_inset
                    + Const.thread_clearance
                )
                / 2,
                length=Const.thread_height,
                mode=Mode.SUBTRACT,
                **Const.thread_args,  # ty: ignore[invalid-argument-type]
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
                root_radius=(Const.diameter - Const.thread_inset) / 2,
                length=Const.thread_height * 2,
                mode=Mode.ADD,
                **Const.thread_args,  # ty: ignore[invalid-argument-type]
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


class RGBLight(Model):
    def build(self) -> Compound:
        with BuildPart() as fixture_base:
            BodyHalf(
                height=Const.base_height,
                rotation=(0, 180, 0),
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
