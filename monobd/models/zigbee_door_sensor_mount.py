from __future__ import annotations

from functools import cached_property
from operator import itemgetter
from typing import cast

from bdbox import Model
from build123d import (
    MM,
    Align,
    Axis,
    BasePartObject,
    Box,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    CounterSinkHole,
    GridLocations,
    Location,
    Locations,
    Mode,
    Plane,
    RotationLike,
    Select,
    chamfer,
    extrude,
    fillet,
    mirror,
    validate_inputs,
)

from monobd.objects.hatches import HatchPattern

first_and_last = itemgetter(0, -1)


class DoubleEndedScrewHole(BasePartObject):
    def __init__(
        self,
        screw_size: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
        depth: float | None = None,
    ) -> None:
        context: BuildPart | None = BuildPart._get_context(self)  # noqa: SLF001
        validate_inputs(context, self)
        if depth is not None:
            hole_depth = depth * 2
        elif depth is None and context is not None:
            hole_depth = context.max_dimension
        else:
            raise ValueError("No depth provided")
        with (
            BuildPart() as p,
            Locations((0, 0, hole_depth / 4)),
        ):
            hole = CounterSinkHole(
                radius=screw_size / 2,
                counter_sink_radius=screw_size,
                depth=hole_depth / 2,
                mode=Mode.ADD,
            )
            mirror(hole, about=Plane.XY)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SensorMountCover(BasePartObject):
    def __init__(
        self,
        sensor_size: tuple[float, float, float],
        thickness: float,
        screw_size: float,
        cover_screw_size: float,
        fit: float,
        sensor_fillet: float = 0.6 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        placement_location = Location((screw_size / 1 + thickness / 2, 0, 0))
        case_width = sensor_size[0] + thickness * 3 + screw_size * 2
        case_depth = sensor_size[1] + thickness * 2
        with BuildPart() as p:
            with Locations(placement_location):
                Box(
                    case_width,
                    case_depth,
                    thickness * 1.5,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            fillet(p.edges().filter_by(Axis.Z), radius=thickness * 2)
            chamfer(p.edges().group_by(Axis.Z)[0], thickness)
            if not p.part:
                raise RuntimeError("Empty part")
            with Locations(Plane.XY.offset(p.part.bounding_box().size.Z)):
                Box(
                    sensor_size[0] - fit,
                    sensor_size[1] - fit,
                    thickness,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.ADD,
                )
            fillet(p.edges().filter_by(Axis.Z), sensor_fillet)
            fillet(p.edges().group_by(Axis.Z)[-1], sensor_fillet)
            with Locations(placement_location):
                with BuildSketch() as sk:
                    HatchPattern(
                        sensor_size[0] - thickness * 2,
                        sensor_size[1] - thickness * 2,
                        4.8 * MM,
                        hatch_rotation=30,
                    )
                extrude(sk.sketch, thickness * 2.5, mode=Mode.SUBTRACT)
            # Cover screw holes
            with (
                Locations(-Plane.XY),
                Locations(
                    (
                        sensor_size[0] / 2 + thickness + screw_size,
                        0,
                        0,
                    )
                ),
                GridLocations(0, sensor_size[1] / 2, 1, 2),
            ):
                CounterSinkHole(
                    radius=cover_screw_size / 2,
                    counter_sink_radius=cover_screw_size,
                )

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SensorMountCase(BasePartObject):
    def __init__(
        self,
        sensor_size: tuple[float, float, float],
        thickness: float,
        screw_size: float,
        insert_diameter: float,
        sensor_fillet: float = 0.6 * MM,
        screw_hole_spacing: float = 0,
        screw_hole_offset: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ) -> None:
        placement_location = Location((screw_size / 1 + thickness / 2, 0, 0))
        case_width = sensor_size[0] + thickness * 3 + screw_size * 2
        case_depth = sensor_size[1] + thickness * 2
        with BuildPart() as p:
            with Locations(placement_location):
                Box(
                    case_width,
                    case_depth,
                    sensor_size[2] + thickness * 2,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            fillet(p.edges().filter_by(Axis.Z), radius=thickness * 2)
            chamfer(p.edges().group_by(Axis.Z)[-1], thickness)
            Box(
                sensor_size[0],
                sensor_size[1],
                sensor_size[2] + thickness,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
            fillet(p.edges(Select.LAST).filter_by(Axis.Z), sensor_fillet)
            screw_hole_spacing = screw_hole_spacing or sensor_size[2] / 2
            with (
                Locations(
                    Plane.XZ.move(
                        Location(
                            (
                                (sensor_size[0] / 2 + thickness + screw_size),
                                0,
                                sensor_size[2] / 2 + screw_hole_offset,
                            )
                        )
                    )
                ),
                GridLocations(1, screw_hole_spacing, 1, 2),
            ):
                DoubleEndedScrewHole(screw_size, depth=20)
            # Cover screw holes
            with (
                Locations(-Plane.XY),
                Locations((sensor_size[0] / 2 + thickness + screw_size, 0, 0)),
                GridLocations(0, sensor_size[1] / 2, 1, 2),
            ):
                depth = (
                    (sensor_size[2] / 2 - screw_hole_spacing / 2)
                    - screw_size
                    - thickness / 2
                    + screw_hole_offset
                )
                CounterSinkHole(
                    radius=insert_diameter / 2,
                    counter_sink_radius=insert_diameter * (0.75),
                    depth=depth,
                    mode=Mode.SUBTRACT,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ZigbeeModel(Model):
    fit: float = 0.4 * MM
    thickness: float = 1.8 * MM
    screw_size: float = 4.75 * MM
    cover_screw_size: float = 3.2 * MM
    insert_diameter: float = 4.6 * MM
    height_factor: int = 1
    sensor_fit: float = 0.2 * MM
    sensor_fillet: float = 0.6 * MM

    @cached_property
    def sensor_mount(self) -> Compound:
        base_sensor_size = (25 * MM, 20 * MM, 71 * MM)
        sensor_size = cast(
            "tuple[float, float, float]",
            tuple(
                i + self.sensor_fillet + self.sensor_fit
                for i in base_sensor_size
            ),
        )
        placement_location = Location(
            (self.screw_size / 1 + self.thickness / 2, 0, 0)
        )
        pb = SensorMountCover(
            sensor_size,
            self.thickness,
            self.screw_size,
            self.cover_screw_size,
            self.fit,
        )
        pb = pb.move(
            Location((0, 0, -(pb.bounding_box().size.Z - self.thickness)))
        )
        p = SensorMountCase(
            sensor_size, self.thickness, self.screw_size, self.insert_diameter
        )
        p.label = "sensor_mount"
        p.color = Color(0xEEFFFF, alpha=0x99)
        pb.label = "cover"
        pb.color = Color(0x22FF88, alpha=0x99)
        return Compound(label="sensor_mount", children=[p, pb]).move(
            Location((placement_location.position.X, 0, 0))
        )

    @cached_property
    def magnet_mount(self) -> Compound:
        base_sensor_size = (10 * MM, 17 * MM, 36 * MM)
        sensor_size = cast(
            "tuple[float, float, float]",
            tuple(
                i + self.sensor_fillet + self.sensor_fit
                for i in base_sensor_size
            ),
        )
        placement_location = Location(
            (self.screw_size / 1 + self.thickness / 2, 0, 0)
        )
        pb = SensorMountCover(
            sensor_size,
            self.thickness,
            self.screw_size,
            self.cover_screw_size,
            self.fit,
        )
        pb = pb.move(
            Location((0, 0, -(pb.bounding_box().size.Z - self.thickness)))
        )

        p = SensorMountCase(
            sensor_size,
            self.thickness,
            self.screw_size,
            self.insert_diameter,
            screw_hole_spacing=sensor_size[2] / 3,
            screw_hole_offset=5 * MM,
        )
        p.label = "magnet_mount"
        p.color = Color(0xEEFFFF, alpha=0x99)
        pb.label = "cover"
        pb.color = Color(0x22FF88, alpha=0x99)
        return Compound(label="magnet_mount", children=[p, pb]).move(
            Location((placement_location.position.X, 0, 0))
        )

    def build(self) -> Model.Geometry:
        return Compound(
            label="zigbee_door_sensor_mount",
            children=[
                self.sensor_mount.move(Location((0, 0, 0))),
                self.magnet_mount.move(
                    Location((-30 * MM, 0, 0), (0, 0, 180))
                ),
            ],
        )
