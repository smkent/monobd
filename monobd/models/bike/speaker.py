from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from operator import itemgetter

from bdbox import Model
from build123d import (
    MM,
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    CounterBoreHole,
    CounterSinkHole,
    Cylinder,
    GridLocations,
    Hole,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    RectangleRounded,
    Rot,
    RotationLike,
    Select,
    Triangle,
    chamfer,
    extrude,
    fillet,
    make_hull,
    mirror,
    pack,
    split,
)

from monobd.objects import HexagonPattern

first_and_last = itemgetter(0, -1)


@dataclass
class Show(Exception):  # noqa: N818
    geometry: Model.Geometry | None


class StemProfile(BaseSketchObject):
    def __init__(
        self,
        width: float,
        height: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            Rectangle(width, height / 2, align=(Align.CENTER, Align.MIN))
            with Locations((0, height / 2)):
                Circle(
                    radius=width / 2,
                    arc_size=180,
                    align=(Align.CENTER, Align.MIN),
                )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class StemMount(BasePartObject):
    def __init__(
        self,
        stem_diameter: float,
        thickness: float,
        clamp_width: float,
        stem_fit: float,
        top_rise: float,
        top_size: float,
        top_center_diameter: float,
        split_offset: float,
        edge_chamfer: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
        *,
        top: bool = True,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch(Plane.XZ) as sk:
                outer_diameter = stem_diameter + (thickness + stem_fit) * 2
                Circle(radius=outer_diameter / 2)
                with Locations((0, outer_diameter / 2)):
                    Rectangle(
                        top_size,
                        # stem_diameter + thickness * 2,
                        outer_diameter / 2,
                        align=(Align.CENTER, Align.MAX),
                    )
                make_hull()
                try:
                    fillet(
                        sk.vertices().group_by(Axis.Y)[1], outer_diameter / 2
                    )
                except ValueError:
                    print("Fillet failed")  # noqa: T201
                with Locations((0, stem_diameter / 2 + thickness + stem_fit)):
                    Rectangle(
                        top_size, top_rise, align=(Align.CENTER, Align.MIN)
                    )
                    Rectangle(
                        top_center_diameter,
                        top_rise,
                        align=(Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
                try:
                    fillet(
                        sk.vertices(Select.LAST).group_by(Axis.Y)[0],
                        (top_size - top_center_diameter) / 2,
                    )
                except ValueError:
                    print("Fillet failed")  # noqa: T201
            extrude(amount=clamp_width)
            if edge_chamfer > 0:
                fillet(
                    list(p.edges().filter_by(Plane.XZ).group_by(Axis.Z))[:-1],
                    edge_chamfer,
                )

            with BuildSketch(Plane.XZ):
                Circle(radius=stem_diameter / 2 + stem_fit)
            extrude(amount=clamp_width, mode=Mode.SUBTRACT)
            chamfer(p.edges(Select.LAST).filter_by(Plane.XZ), 0.6 * MM)

            split_plane = Plane.XY.offset(split_offset)
            split(bisect_by=(split_plane if top else -split_plane))
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountTopSingleCut(BasePartObject):
    def __init__(
        self,
        thickness: float,
        top_size: float,
        top_thickness: float,
        top_center_diameter: float,
        tab_cut: float = 50 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        outer = top_size + top_thickness
        tab_cut_depth = outer / 2 - top_thickness
        with BuildPart() as p:
            with BuildSketch() as sk:
                Rectangle(outer, outer)
                fillet(sk.vertices().group_by(Axis.Y)[1], outer / 4)
                with Locations((0, -outer / 2)):
                    Rectangle(
                        tab_cut,
                        tab_cut_depth,
                        align=(Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
                fillet(
                    sk.vertices().group_by(Axis.Y)[1],
                    min(tab_cut, tab_cut_depth) / 2,
                )
                fillet(
                    sk.vertices().group_by(Axis.Y)[0],
                    min(outer - top_center_diameter, outer - tab_cut) / 4,
                )
            extrude(amount=top_thickness)
            fillet(
                first_and_last(p.edges().filter_by(Plane.XY).group_by(Axis.Z)),
                top_thickness * 0.49,
            )
            with BuildSketch():
                HexagonPattern(
                    top_center_diameter,
                    top_center_diameter,
                    hex_size=8,
                    whole_only=False,
                    align=(Align.CENTER, Align.CENTER),
                    mode=Mode.ADD,
                )
                with BuildSketch(mode=Mode.INTERSECT):
                    Circle(radius=top_center_diameter / 2)
                    with Locations(
                        (0, -outer / 2 + tab_cut_depth + thickness)
                    ):
                        Rectangle(
                            top_center_diameter,
                            top_center_diameter,
                            align=(Align.CENTER, Align.MIN),
                            mode=Mode.INTERSECT,
                        )
            extrude(amount=top_thickness, mode=Mode.SUBTRACT)

        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountTopDoubleCut(BasePartObject):
    def __init__(
        self,
        top_size: float,
        top_thickness: float,
        top_center_diameter: float,
        tab_cut: float = 40 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        outer = top_size + top_thickness
        tab_cut_depth = (outer / 2 - 10 * MM) - top_thickness
        with BuildPart() as p:
            with BuildSketch() as sk:
                Rectangle(outer, outer / 2, align=(Align.CENTER, Align.MIN))
                with Locations((0, outer / 2)):
                    Rectangle(
                        tab_cut,
                        tab_cut_depth,
                        align=(Align.CENTER, Align.MAX),
                        mode=Mode.SUBTRACT,
                    )
                fillet(
                    sk.vertices().group_by(Axis.Y)[-2],
                    min(tab_cut, tab_cut_depth) / 2,
                )
                fillet(
                    sk.vertices().group_by(Axis.Y)[-1],
                    min(outer - top_center_diameter, outer - tab_cut) / 4,
                )
                mirror(about=Plane.XZ)

            extrude(amount=top_thickness)
            fillet(
                first_and_last(p.edges().filter_by(Plane.XY).group_by(Axis.Z)),
                top_thickness * 0.49 * MM,
            )

            hex_height = outer - tab_cut_depth * 2 - top_thickness * 2
            if hex_height >= 8:
                with BuildSketch():
                    HexagonPattern(
                        top_center_diameter,
                        top_center_diameter,
                        hex_size=8,
                        whole_only=False,
                        align=(Align.CENTER, Align.CENTER),
                        mode=Mode.ADD,
                    )
                    RectangleRounded(
                        top_center_diameter,
                        hex_height,
                        hex_height / 4,
                        align=(Align.CENTER, Align.CENTER),
                        mode=Mode.INTERSECT,
                    )
                extrude(amount=top_thickness, mode=Mode.SUBTRACT)

        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BikeSpeakerMount(Model):
    print_orientation: bool = True
    stem_diameter_mm: float = 32
    thickness_mm: float = 6
    clamp_width_mm: float = 15
    screw_size_mm: float = 3
    insert_size_mm: float = 4.7
    stem_fit_mm: float = 1
    stem_mount_trim_mm: float = 0
    screw_fit_mm: float = 0.4
    top_rise_mm: float = 20
    top_size_mm: float = 64
    top_center_diameter_mm: float = 40
    top_thickness_mm: float = 10
    top_angle: float = 10
    top_style_single_cut: bool = False
    edge_chamfer_mm: float = 3
    split_offset_ratio: float = 0.10

    @cached_property
    def stem_diameter(self) -> float:
        return self.stem_diameter_mm * MM

    @cached_property
    def screw_size(self) -> float:
        return (self.screw_size_mm + self.screw_fit_mm) * MM

    @cached_property
    def top_screw_spacing(self) -> float:
        return (self.top_center_diameter_mm + self.top_size_mm * MM) / 2

    @cached_property
    def bottom_screw_spacing(self) -> float:
        return self.stem_diameter + self.screw_size * 4

    @cached_property
    def top_rise(self) -> float:
        return (
            self.top_rise_mm + self.top_rise_mm * math.radians(self.top_angle)
        ) * MM

    @cached_property
    def split_offset(self) -> float:
        return self.stem_diameter * self.split_offset_ratio

    @cached_property
    def stem_mount_top(self) -> Part:
        with BuildPart() as p:
            with Locations((0, 0, self.stem_mount_trim_mm * MM)):
                StemMount(
                    self.stem_diameter,
                    self.thickness_mm * MM,
                    self.clamp_width_mm * MM,
                    self.stem_fit_mm * MM,
                    (
                        self.top_rise_mm
                        + self.top_rise_mm * math.radians(self.top_angle)
                    )
                    * MM,
                    self.top_size_mm * MM,
                    self.top_center_diameter_mm * MM,
                    self.split_offset + self.stem_mount_trim_mm * MM,
                    self.edge_chamfer_mm * MM,
                    top=True,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                if not p.part:
                    raise RuntimeError("Empty part")
                with (
                    Locations(-Plane.XY),
                    GridLocations(self.bottom_screw_spacing, 0, 2, 1),
                ):
                    CounterSinkHole(
                        self.insert_size_mm * MM / 2,
                        (self.insert_size_mm + 2) * MM / 2,
                        15 * MM - self.split_offset,
                    )
            top = p.part.bounding_box().max.Z

            if self.top_angle:
                with (
                    BuildSketch(Plane.YZ),
                    Locations((-self.clamp_width_mm / 2 * MM, top)),
                ):
                    Triangle(
                        a=self.clamp_width_mm * MM,
                        C=90,
                        B=self.top_angle,
                        align=(Align.MAX, Align.MIN),
                        rotation=180,
                    )
                extrude(
                    amount=self.top_size_mm / 2 * MM,
                    both=True,
                    mode=Mode.SUBTRACT,
                )

            with (
                Locations(
                    Plane.XY.offset(
                        top
                        - self.top_rise_mm * MM * math.radians(self.top_angle)
                    )
                ),
                GridLocations(
                    self.top_screw_spacing, (self.top_size_mm / 3) * MM, 2, 3
                ),
            ):
                Hole(self.insert_size_mm * MM / 2, depth=self.top_rise_mm * MM)
                chamfer(p.edges(Select.LAST).group_by(Axis.Z)[-1], 1 * MM)

        p.part.label = "stem_mount_top"
        part = p.part
        if self.print_orientation:
            part = Rot(-90, 0, 0) * part
        return part

    @cached_property
    def stem_mount_bottom(self) -> Part:
        with BuildPart() as p:
            StemMount(
                self.stem_diameter,
                self.thickness_mm * MM,
                self.clamp_width_mm * MM,
                self.stem_fit_mm * MM,
                self.top_rise_mm * MM,
                self.top_size_mm * MM,
                self.top_center_diameter_mm * MM,
                self.split_offset,
                self.edge_chamfer_mm * MM,
                top=False,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )
            with (
                GridLocations(self.bottom_screw_spacing, 0, 2, 1),
                Locations(
                    -Plane.XY.offset(
                        -(self.stem_diameter / 4 + self.split_offset)
                    )
                ),
            ):
                CounterBoreHole(
                    self.screw_size / 2,
                    self.screw_size,
                    self.screw_size * (1 + self.split_offset_ratio * 2),
                )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "stem_mount_bottom"
        part = p.part
        if self.print_orientation:
            part = Rot(-90, 0, 0) * part
        return part

    @cached_property
    def mount(self) -> Part:
        with BuildPart() as p:
            if self.top_style_single_cut:
                MountTopSingleCut(
                    thickness=self.thickness_mm * MM,
                    top_size=self.top_size_mm * MM,
                    top_thickness=self.top_thickness_mm * MM,
                    top_center_diameter=self.top_center_diameter_mm * MM,
                )
            else:
                MountTopDoubleCut(
                    top_size=self.top_size_mm * MM,
                    top_thickness=self.top_thickness_mm * MM,
                    top_center_diameter=self.top_center_diameter_mm * MM,
                )
            with (
                Locations(Plane.XY.offset(self.top_thickness_mm * MM)),
                GridLocations(
                    self.top_screw_spacing, (self.top_size_mm / 3) * MM, 2, 1
                ),
                Locations(
                    Location(
                        (
                            0,
                            0,
                            -self.screw_size * math.radians(self.top_angle),
                        ),
                        (-self.top_angle, 0, 0),
                    )
                ),
            ):
                CounterSinkHole(self.screw_size / 2, self.screw_size)

        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "speaker_mount_platform"
        part = p.part
        if not self.print_orientation:
            part.move(Location((0, 0, 0 * -self.top_thickness_mm / 2 * MM)))
            part = part.rotate(
                Axis((0, 0, self.top_thickness_mm / 2 * MM), Axis.X.direction),
                self.top_angle,
            )
            part.move(
                Location(
                    Plane.XY.offset(
                        -self.top_thickness_mm
                        * MM
                        * math.radians(self.top_angle)
                    )
                )
            )
        return part

    def build(self) -> Model.Geometry | None:
        try:
            with BuildPart() as tube, Locations((0, 0, -self.split_offset)):
                Cylinder(
                    radius=self.stem_diameter / 2,
                    height=self.stem_diameter * 2,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                )
            if not tube.part:
                raise RuntimeError("Empty part")
            tube.part.label = "stem"
            tube.part.color = Color(0x333333, alpha=0xCC)
            stem_mount_top = self.stem_mount_top
            parts = [
                self.stem_mount_top,
                self.stem_mount_bottom,
                self.mount.move(
                    Location((0, 0, stem_mount_top.bounding_box().max.Z))
                ),
            ]
            if self.print_orientation:
                if len(parts) > 1:
                    parts = pack(parts, padding=5 * MM)
                    for part in parts:
                        part.move(Location((0, 0, -part.bounding_box().min.Z)))
            else:
                parts.append(tube.part)
            return Compound(children=list(parts))
        except Show as e:
            return e.geometry
