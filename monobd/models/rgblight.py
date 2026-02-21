from __future__ import annotations

from bd_warehouse.thread import Thread
from bdbox import Model
from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BuildPart,
    Color,
    Compound,
    Cylinder,
    Location,
    Locations,
    Mode,
    Select,
    chamfer,
    fillet,
)


class RGBLight(Model):
    diameter: float = 2 * IN
    base_height = 1 * IN
    led_mount_diameter = 0.5 * IN
    led_mount_height = 1 * IN

    thread_inset = 0.5 * IN
    thread_height = 0.25 * IN
    thread_clearance = 2  # 0.25 * MM

    thickness: float = (1 + 1 / 8) * IN
    screw_size: float = (1 / 4) * IN
    chamfer: float = (1 / 16) * IN
    slop: float = (1 / 32) * IN

    def build(self) -> Compound:
        thickness = 1.6 * MM  # self.thread_inset / 2
        with BuildPart() as p:
            Cylinder(
                self.diameter / 2,
                self.base_height - self.thread_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            fillet(
                p.edges(Select.LAST).group_by(Axis.Z)[0], self.base_height / 3
            )

            with BuildPart(mode=Mode.SUBTRACT) as p_sub:
                with Locations((0, 0, thickness)):
                    Cylinder(
                        self.diameter / 2 - thickness,
                        self.base_height - self.thread_height - thickness * 2,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                last_edges = p_sub.edges(Select.LAST)
                fillet(
                    last_edges.group_by(Axis.Z)[0],
                    self.base_height / 3 - thickness * 1,
                )
                chamfer(
                    last_edges.group_by(Axis.Z)[-1],
                    (
                        (self.base_height - self.thread_height)
                        - (self.base_height / 3 - thickness * 1)
                    )
                    / 2,
                    # self.base_height / 3 - thickness * 1,
                )

                # Bottom cutout
                Cylinder(
                    self.diameter / 2
                    - thickness
                    - (self.base_height / 3 - thickness * 1)
                    - thickness * 4,
                    thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

            with Locations(p.faces().sort_by(Axis.Z)[-1]):
                Thread(
                    apex_radius=(self.diameter - self.thread_inset / 2) / 2,
                    apex_width=2,
                    root_radius=(self.diameter - self.thread_inset) / 2,
                    root_width=4,
                    pitch=8,
                    length=self.thread_height,
                    end_finishes=("chamfer", "chamfer"),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                Cylinder(
                    (self.diameter - self.thread_inset + 0.1) / 2,
                    self.thread_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

            # Mid-thread cutout
            with Locations(
                (0, 0, self.base_height - self.thread_height - thickness)
            ):
                Cylinder(
                    (self.diameter - self.thread_inset + 0.1) / 2 - thickness,
                    self.thread_height + thickness * 2,
                    mode=Mode.SUBTRACT,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

            with Locations((0, 0, self.base_height)):
                Cylinder(
                    self.led_mount_diameter / 2,
                    self.led_mount_height - thickness * 2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )

        p.part.label = "base"
        p.part.color = Color(0x11AACC, alpha=0xCC)

        with BuildPart() as p2:
            Cylinder(
                self.diameter / 2,
                (self.thread_height + self.led_mount_height),
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            fillet(
                p2.edges(Select.LAST).group_by(Axis.Z)[-1],
                self.base_height / 3,
            )

            with BuildPart(mode=Mode.SUBTRACT) as p2_sub:
                with Locations((0, 0, self.thread_height)):
                    Cylinder(
                        self.diameter / 2 - thickness,
                        self.led_mount_height - thickness * 1,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                fillet(
                    p2_sub.edges(Select.LAST).group_by(Axis.Z)[-1],
                    self.base_height / 3 - thickness * 1,
                )

            Cylinder(
                (self.diameter - self.thread_inset + 0.1) / 2,
                (self.thread_height),
                mode=Mode.SUBTRACT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

            Thread(
                apex_radius=(self.diameter - self.thread_inset / 2) / 2,
                apex_width=2,
                root_radius=(
                    self.diameter - self.thread_inset + self.thread_clearance
                )
                / 2,
                root_width=4,
                pitch=8,
                length=self.thread_height,
                end_finishes=("chamfer", "chamfer"),
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        p2.part.label = "top"
        p2.part.color = Color(0xDDDDDD, alpha=0xCC)
        p2.part = p2.part.move(
            Location((0, 0, self.base_height - self.thread_height))
        )

        return Compound(children=[p.part, p2.part])
