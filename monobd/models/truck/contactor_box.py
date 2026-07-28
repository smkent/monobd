from __future__ import annotations

from contextlib import contextmanager
from functools import cached_property
from operator import itemgetter
from typing import TYPE_CHECKING

from bdbox import Model
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
    Color,
    Cylinder,
    GridLocations,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Vector,
    extrude,
    fillet,
    offset,
)

from monobd.print_utils import arrange

if TYPE_CHECKING:
    from collections.abc import Iterator

first_and_last = itemgetter(0, -1)


class Box:
    size = Vector(256 * MM, 176 * MM, 75 * MM)
    wall_thickness = 5 * MM
    mid_column = Vector(20 * MM, 13 * MM)
    end_column = Vector(10 * MM, 20 * MM)
    end_column_radius = 6 * MM

    mount_hole_radius = 2 * MM
    mount_hole_position = Vector(238 * MM, 74 * MM)

    class Wire:
        large_wire_radius = (17 * MM) / 2
        connector_radius = (35 * MM) / 2

    @classmethod
    @contextmanager
    def insert_standoff_locations(cls) -> Iterator[None]:
        with GridLocations(
            cls.mount_hole_position.X, cls.mount_hole_position.Y, 2, 2
        ):
            yield

    @classmethod
    @contextmanager
    def standoff_locations(cls) -> Iterator[None]:
        locs = []
        locs.extend(
            GridLocations(
                cls.mount_hole_position.X / 2,
                cls.mount_hole_position.Y / 2,
                3,
                3,
            ).locations
        )
        with (
            GridLocations(20 * MM, 0, 4, 1),
            GridLocations(
                cls.size.X - 2 * 66 * MM, cls.size.Y - 2 * 8 * MM, 2, 2
            ) as gl,
        ):
            locs.extend(gl.locations)

        with Locations(locs):
            yield


class BaseProfileCutouts(BaseSketchObject):
    def __init__(
        self,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        with BuildSketch() as sk:
            with BuildSketch(), GridLocations(0, Box.size.Y, 1, 2):
                RectangleRounded(
                    Box.mid_column.X,
                    Box.mid_column.Y * 2,
                    radius=Box.mid_column.X * 0.499,
                )
            with GridLocations(Box.size.X, Box.size.Y, 2, 2):
                RectangleRounded(
                    Box.end_column.X * 2,
                    Box.end_column.Y * 2,
                    radius=Box.end_column_radius,
                )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class BaseProfile(BaseSketchObject):
    def __init__(
        self,
        edge_fit: float = 0,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            Rectangle(Box.size.X, Box.size.Y)
            BaseProfileCutouts(mode=Mode.SUBTRACT)
            verts = [
                *first_and_last(sk.vertices().group_by(Axis.X)),
                *first_and_last(sk.vertices().group_by(Axis.Y)),
            ]
            fillet(verts, 2 * MM)
            offset(amount=-edge_fit)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class Base(BasePartObject):
    def __init__(
        self,
        thickness: float,
        edge_fit: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch():
                BaseProfile(edge_fit)
                with Box.insert_standoff_locations():
                    Circle(radius=Box.mount_hole_radius, mode=Mode.SUBTRACT)
            extrude(amount=thickness)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ContactorBoxMount(Model):
    print_orientation: bool = False
    thickness: float = 5 * MM
    edge_fit: float = 1 * MM

    @cached_property
    def box(self) -> Part:
        with BuildPart() as p:
            with BuildSketch():
                Rectangle(Box.size.X, Box.size.Y)
                offset(amount=Box.wall_thickness)
            extrude(amount=Box.size.Z)
            with BuildSketch(Plane.XY.offset(Box.wall_thickness)):
                BaseProfile()
            extrude(amount=Box.size.Z, mode=Mode.SUBTRACT)
            with (
                BuildSketch(Plane.XY.offset(Box.wall_thickness)),
                Box.standoff_locations(),
            ):
                Circle(radius=Box.mount_hole_radius * 3)
                Circle(radius=Box.mount_hole_radius, mode=Mode.SUBTRACT)
            extrude(amount=Box.wall_thickness)
            # Cutouts for large wire connectors
            with (
                Locations((0, 0, Box.size.Z / 2)),
                GridLocations(Box.size.X, Box.size.Y / 2, 2, 2),
            ):
                Cylinder(
                    Box.Wire.connector_radius,
                    height=Box.wall_thickness * 2,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Box outline"
        p.part.color = Color(0xCCCCCC, 0xCC)
        return p.part

    @cached_property
    def large_wires(self) -> Part:
        with (
            BuildPart() as p,
            Locations((0, 0, Box.size.Z / 2)),
            GridLocations(0, Box.size.Y / 2, 1, 2),
        ):
            Cylinder(
                Box.Wire.large_wire_radius,
                height=Box.size.X * 1.5,
                rotation=(0, 90, 0),
            )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Large wires"
        p.part.color = Color(0xFF5511, 0xAA)
        return p.part

    @cached_property
    def plate(self) -> Part:
        with BuildPart() as p:
            Base(thickness=self.thickness, edge_fit=self.edge_fit)
            # Shunt mount
            with (
                BuildSketch(),
                Locations((-Box.size.X / 4, -Box.size.Y / 4, 0)),
                GridLocations(0, (1.25 * IN), 1, 2),
            ):
                Circle(radius=(6 * MM) / 2)
            extrude(amount=self.thickness, mode=Mode.SUBTRACT)
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Box plate"
        return p.part.move(Location((0, 0, Box.wall_thickness * 2)))

    def build(self) -> Model.Geometry:
        return arrange(
            self.large_wires,
            self.plate,
            self.box,
            pack_parts=self.print_orientation,
        )
