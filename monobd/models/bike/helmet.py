from __future__ import annotations

import math
from functools import cached_property
from operator import itemgetter
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, TypeVar

from bdbox import Model
from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BaseEdgeObject,
    BasePartObject,
    BaseSketchObject,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Color,
    EllipticalCenterArc,
    Face,
    GeomType,
    GridLocations,
    Line,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Polyline,
    RadiusArc,
    Rectangle,
    RotationLike,
    Select,
    SortBy,
    Vector,
    VectorLike,
    add,
    chamfer,
    extrude,
    fillet,
    loft,
    make_face,
    mirror,
    offset,
    sweep,
)

from monobd.print_utils import PrintRotation, arrange

if TYPE_CHECKING:
    from collections.abc import Callable

    P = ParamSpec("P")
    R = TypeVar("R")

    F = Callable[Concatenate[Any, P], R]


first_and_last = itemgetter(0, -1)


class RailSize:
    bottom_width = 2.0
    bottom_height = 2.4
    top_width = 4.4
    top_height = 1.6
    spacing = 6.8
    center_recess = 0.2
    height = bottom_height + top_height
    width = max(bottom_width, top_width)
    total_width = spacing + width


class RailGripSize:
    bottom_width = 1.6
    top_width = 0.8
    top_height = 0.4


class StrapGripSize:
    width = 2.6
    length = 22
    outset = 2.0


class RailProfile(BaseSketchObject):
    def __init__(
        self,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                pts = (
                    (0, 0),
                    (RailSize.bottom_width / 2, 0),
                    (RailSize.bottom_width / 2, RailSize.bottom_height),
                    (RailSize.top_width / 2, RailSize.bottom_height),
                    (RailSize.top_width / 2, RailSize.height),
                    (0, RailSize.height),
                    (0, 0),
                )
                Polyline(pts)
            make_face()
            mirror(about=Plane.YZ)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class RailGripProfile(BaseSketchObject):
    def __init__(
        self,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                pts = (
                    (0, 0),
                    (RailGripSize.bottom_width / 2, 0),
                    (RailGripSize.top_width / 2, RailGripSize.top_height),
                    (0, RailGripSize.top_height),
                    (0, 0),
                )
                Polyline(pts)
            make_face()
            mirror(about=Plane.YZ)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class RailGrip(BasePartObject):
    def __init__(
        self,
        length: float = RailSize.top_width,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch(Plane.YZ):
                RailGripProfile(align=(Align.CENTER, Align.MIN))
            extrude(amount=length / 2, both=True)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class Rail(BasePartObject):
    def __init__(
        self,
        length: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            # Basic profile
            with BuildSketch(Plane.XZ):
                RailProfile(align=(Align.CENTER, Align.MIN))
            extrude(amount=length / 2, both=True)
            # Horizontal intersection profile
            with BuildSketch(Plane.YZ) as sk:
                pts = (
                    (0, 0),
                    (0, RailSize.height),
                    (
                        length / 2 - RailSize.height * (2 / 3),
                        RailSize.height,
                    ),
                    (length / 2, 0),
                    (0, 0),
                )
                Polygon(pts)
                mirror(about=Plane.YZ)
                fillet(
                    sk.vertices().sort_by_distance((0, 0))[:-2],
                    RailSize.height,
                )
            extrude(amount=RailSize.width / 2, both=True, mode=Mode.INTERSECT)
            # Vertical intersection profile
            with BuildSketch() as sk:
                Rectangle(RailSize.width, length - RailSize.bottom_width * 2)
                chamfer(
                    sk.vertices(),
                    (RailSize.top_width - RailSize.bottom_width) / 2,
                )
                Rectangle(RailSize.bottom_width, length)
                mid_vertices = sk.vertices().sort_by_distance((0, 0))[:-4]
                fillet(mid_vertices, RailSize.top_width / 8)
            extrude(amount=RailSize.height, mode=Mode.INTERSECT)
            # Retention clips
            with (
                Locations((0, 0, RailSize.height)),
            ):
                RailGrip(align=(Align.CENTER, Align.CENTER, Align.MIN))
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class Rails(BasePartObject):
    def __init__(
        self,
        length: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p, GridLocations(RailSize.spacing, 0, 2, 1):
            Rail(length=length)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class RiserProfile(BaseSketchObject):
    def __init__(
        self,
        width: float,
        height: float,
        base_thickness: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                in_w = RailSize.total_width * 1.5 / 2
                out_w = width / 2
                h = height
                arc_w = out_w - in_w
                arc = EllipticalCenterArc(
                    (arc_w + in_w, h),
                    arc_w,
                    h,
                    arc_size=90,
                    start_angle=180,
                )
                Polyline((0, h), (in_w, h), arc @ 0)
                Polyline(
                    arc @ 1,
                    ((arc @ 1).X, -base_thickness),
                    (0, -base_thickness),
                )
                mirror(about=Plane.YZ)
            make_face()
            fillet(
                sk.vertices().filter_by_position(Axis.Y, 0.001, h),
                RailSize.total_width * 0.5,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class MountTop(BasePartObject):
    def __init__(
        self,
        base_size: float,
        rail_size: float,
        thickness: float,
        riser_thickness: float,
        screw_size: float,
        slider_top_thickness: float,
        slider_grip_thickness: float,
        edge_chamfer: float = 0.4 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        with BuildPart() as p:
            SliderTop(
                base_size,
                slider_top_thickness,
                slider_grip_thickness,
                thickness,
                riser_thickness,
                screw_size,
                edge_chamfer=edge_chamfer,
                fancy=fancy,
            )
            Rails(
                length=rail_size, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            if not p.part:
                raise RuntimeError("Missing part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class TiltCurve(BaseEdgeObject):
    def __init__(
        self,
        base_width: float,
        width: float | None = None,
        radius: float | None = None,
        center: VectorLike = (0, 0),
        mode: Mode = Mode.ADD,
    ) -> None:
        arc_width = width or base_width
        arc_radius = radius or base_width * 2
        arc_center = tuple(
            Vector((0, math.sqrt(arc_radius**2 - (base_width / 2) ** 2)))
            + Vector(center)
        )
        angle = math.degrees(2 * math.asin((arc_width / 2) / arc_radius))
        arc = CenterArc(arc_center, arc_radius, -(90 + angle / 2), angle)
        super().__init__(curve=arc, mode=mode)

    @classmethod
    def mid(cls, base_width: float) -> Vector:
        return cls(base_width=base_width) @ 0.5


class SliderBottomProfile(BaseSketchObject):
    def __init__(
        self,
        width: float,
        base_thickness: float,
        mid_width: float,
        mid_thickness: float,
        screw_chamfer: float = 1,
        tilt_adjustment: float = 0,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
        *,
        center_cutout: bool = False,
    ) -> None:
        with BuildSketch() as sk:
            adj = tilt_adjustment
            Polygon(
                (mid_width / 2, 0),
                (mid_width / 2 - adj, base_thickness + mid_thickness),
                (-mid_width / 2 + adj, base_thickness + mid_thickness),
                (-mid_width / 2, 0),
                (mid_width / 2, 0),
            )
            Rectangle(
                width,
                base_thickness,
                align=(Align.CENTER, Align.MIN),
            )
            if center_cutout:
                with Locations((0, base_thickness)):
                    w = screw_chamfer * (
                        1.001 + min(0.5, tilt_adjustment / 10)
                    )
                    w_small = max(w / 10, 0.4 * MM)
                    h = mid_thickness
                    with Locations((0, w)):
                        Rectangle(
                            w_small,
                            h - w,
                            align=(Align.CENTER, Align.MIN),
                            mode=Mode.SUBTRACT,
                        )
                        Circle(radius=w, mode=Mode.SUBTRACT)
            fillet(
                list(sk.vertices().group_by(Axis.X))[1:-1],
                screw_chamfer,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class SliderTopProfile(BaseSketchObject):
    def __init__(
        self,
        width: float,
        base_thickness: float,
        mid_width: float,
        mid_thickness: float,
        screw_chamfer: float = 1,
        edge_chamfer: float = 0.4 * MM,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MAX),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            Rectangle(
                width,
                base_thickness * 2 + mid_thickness,
                align=(Align.CENTER, Align.MIN),
            )
            SliderBottomProfile(
                width,
                base_thickness,
                mid_width,
                mid_thickness,
                screw_chamfer,
                mode=Mode.SUBTRACT,
            )
            # Outer corner fillet
            fillet(
                first_and_last(
                    sk.vertices().group_by(Axis.Y)[0].group_by(Axis.X)
                ),
                edge_chamfer * 2,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class SliderSideProfile(BaseSketchObject):
    def __init__(
        self,
        width: float,
        height: float,
        rotation: float = 0,
        align: tuple[Align, Align] | None = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
        *,
        top: bool = True,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                arc = TiltCurve(width, center=((0, height) if top else (0, 0)))
                Polyline(
                    arc @ 0,
                    ((arc @ 0).X, 0 if top else height),
                    ((arc @ 1).X, 0 if top else height),
                    arc @ 1,
                )
            make_face()
        super().__init__(
            obj=sk.sketch,
            rotation=rotation,
            align=align
            or (
                (Align.CENTER, Align.MIN) if top else (Align.CENTER, Align.MAX)
            ),
            mode=mode,
        )


class SliderSlotProfile(BaseSketchObject):
    def __init__(
        self,
        base_width: float,
        width: float,
        height: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine() as ln:
                TiltCurve(base_width, width)
                offset(ln.line, amount=height / 2)
            make_face()
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class SliderScrewHoleProfile(BaseSketchObject):
    def __init__(
        self,
        base_width: float,
        height: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk, Locations(TiltCurve.mid(base_width)):
            Circle(radius=height / 2)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class SliderTopSlotLips(BasePartObject):
    lip_offset: float

    def __init__(
        self,
        base_size: float,
        mid_thickness: float,
        screw_size: float,
        screw_chamfer: float = 1 * MM,
        edge_chamfer: float = 0.4 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ) -> None:
        self.lip_offset = min(
            (base_size * 1 / 4 - screw_size) / 2 - edge_chamfer,  # X
            (mid_thickness - screw_size) * 0.45 - edge_chamfer,  # Y
        )
        with BuildSketch(mode=Mode.PRIVATE) as profile:
            SliderSlotProfile(
                base_size,
                base_size * 3 / 4,
                screw_size,
                align=(Align.CENTER, Align.MIN),
            )
        with BuildPart() as p:
            with BuildSketch(Plane.YZ.offset(base_size / 2)):
                add(offset(profile.sketch, amount=self.lip_offset))
            extrude(amount=-screw_chamfer * 2)
            with BuildSketch(Plane.YZ.offset(base_size / 2)):
                add(offset(profile.sketch, amount=self.lip_offset))
            with BuildSketch(
                Plane.YZ.offset(base_size / 2 + screw_chamfer * 1)
            ):
                add(
                    offset(
                        profile.sketch,
                        amount=self.lip_offset - screw_chamfer / 2,
                    )
                )
            loft()
            mirror(about=Plane.YZ)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SliderTop(BasePartObject):
    def __init__(
        self,
        base_size: float,
        base_thickness: float,
        grip_thickness: float,
        mid_thickness: float,
        riser_thickness: float,
        screw_size: float,
        screw_chamfer: float = 1 * MM,
        edge_chamfer: float = 0.4 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MAX,
        ),
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        curve_thickness = abs(TiltCurve.mid(base_size).Y)
        mid_width = base_size - grip_thickness * 2
        part_z = base_thickness + curve_thickness + mid_thickness
        slot_z = part_z - (mid_thickness / 2 - screw_size / 2)
        with BuildPart() as p:
            with BuildSketch(Plane.XZ), Locations((0, -curve_thickness)):
                SliderTopProfile(
                    base_size,
                    base_thickness,
                    mid_width,
                    mid_thickness,
                    edge_chamfer=edge_chamfer,
                )
            with BuildLine(Plane.YZ) as ln:
                TiltCurve(base_size)
            sweep(path=ln.line, normal=(0, 1, 0))
            with BuildSketch(Plane.YZ):
                SliderSideProfile(
                    base_size,
                    base_thickness,
                    top=False,
                    align=(Align.CENTER, Align.MAX),
                )
            extrude(amount=base_size / 2, both=True)

            with BuildSketch(Plane.XZ.offset(-base_size / 2)):
                RiserProfile(base_size, riser_thickness, base_thickness)
            extrude(amount=base_size)
            fillet(
                p.edges(Select.LAST).filter_by(Axis.Y).group_by(Axis.Z)[0],
                min(riser_thickness + base_thickness, grip_thickness),
            )
            if fancy:
                fillet(
                    first_and_last(
                        p.edges().filter_by(Plane.XZ).group_by(Axis.Y)
                    ),
                    edge_chamfer / 1,
                )
            if fancy:
                with Locations((0, 0, -slot_z)):
                    SliderTopSlotLips(
                        base_size,
                        mid_thickness,
                        screw_size,
                        screw_chamfer,
                        edge_chamfer,
                    )
            with BuildSketch(Plane.YZ), Locations((0, -slot_z, 0)):
                SliderSlotProfile(
                    base_size,
                    base_size * 3 / 4,
                    screw_size,
                    align=(Align.CENTER, Align.MIN),
                )
            extrude(amount=base_size, both=True, mode=Mode.SUBTRACT)
            chamfer(
                p.edges(Select.LAST).filter_by(Plane.YZ),
                screw_chamfer / 2,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SliderStrapGrip(BasePartObject):
    def __init__(
        self,
        base_size: float,
        height: float,
        outset: float,
        grip_width: float = StrapGripSize.width,
        grip_length: float = StrapGripSize.length,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.MAX,
            Align.CENTER,
            Align.MAX,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildLine(Plane.XZ) as ln:
                inset = min(StrapGripSize.width * 4, base_size / 3)
                Polyline(
                    (outset, 0),
                    (-inset, 0),
                    (-inset, -height),
                    (outset, -height),
                )
                fillet(ln.vertices(), height * 0.499)
            with BuildSketch(Plane.YZ):
                with BuildLine():
                    curve_proportion = 0.15
                    w = grip_width
                    h = grip_length
                    arc = EllipticalCenterArc(
                        (h / 2 * (1 - curve_proportion), -w / 2),
                        h / 2 * curve_proportion,
                        w / 2,
                        arc_size=180,
                        start_angle=-90,
                    )
                    Line(arc @ 0, (0, (arc @ 0).Y))
                    Line(arc @ 1, (0, (arc @ 1).Y))
                    mirror(about=Plane.YZ)
                make_face()
            sweep(path=ln.line)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SliderStrapGrips(BasePartObject):
    def __init__(
        self,
        base_size: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MAX,
        ),
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        with BuildPart() as p:
            outset = base_size / 2
            with Locations((base_size / 2 + outset, 0, 0)):
                SliderStrapGrip(
                    base_size=base_size, outset=outset, height=height
                )
            mirror(about=Plane.YZ)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class SliderBase(BasePartObject):
    def __init__(
        self,
        base_size: float,
        base_thickness: float,
        grip_thickness: float,
        slider_fit: float,
        mid_thickness: float,
        screw_size: float,
        screw_chamfer: float = 1 * MM,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        curve_thickness = abs(TiltCurve.mid(base_size).Y)
        mid_width = base_size - grip_thickness * 2
        with BuildPart() as p:
            with BuildLine(Plane.YZ) as ln:
                TiltCurve(base_size)
            with BuildSketch(Plane.XZ):
                SliderBottomProfile(
                    base_size,
                    base_thickness,
                    mid_width,
                    mid_thickness,
                    center_cutout=True,
                )
            sweep(path=ln.line, normal=(0, 1, 0))
            with BuildSketch(Plane.YZ):
                SliderSideProfile(
                    base_size,
                    curve_thickness + base_thickness,
                    top=True,
                )
            extrude(amount=base_size / 2, both=True)

            # Screw hole
            with (
                BuildSketch(Plane.YZ),
                Locations(
                    (0, base_thickness + mid_thickness / 2 + slider_fit)
                ),
            ):
                Circle(screw_size / 2)
            extrude(amount=base_size / 2, both=True, mode=Mode.SUBTRACT)
            chamfer(
                p.edges(Select.LAST).filter_by(
                    lambda edge: (
                        edge.geom_type
                        in (
                            GeomType.BSPLINE,
                            GeomType.CYLINDER,
                            GeomType.CIRCLE,
                        )
                    )
                ),
                min(screw_chamfer, mid_thickness - screw_size) * 0.49,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountBottom(BasePartObject):
    def __init__(
        self,
        base_size: float,
        base_thickness: float,
        bottom_thickness: float,
        bottom_extension: float = 0,
        helmet_curve_radius: float = 10 * IN,
        edge_chamfer: float = 0.4 * MM,
        strap_radius: float = 8 * MM,
        tilt_angle: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MAX,
        ),
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        bottom_thickness -= (
            math.tan(math.radians(tilt_angle / 2)) * StrapGripSize.width
        )
        with BuildPart() as p:
            with BuildLine() as ln:
                tilt = -math.tan(math.radians(tilt_angle)) * base_size / 2
                ww = base_size + bottom_extension
                with BuildLine(Plane.YZ):
                    RadiusArc(
                        (-base_size / 2, tilt / 2, ww / 2),
                        (base_size / 2, -tilt / 2, ww / 2),
                        helmet_curve_radius,
                    )
                    mirror(about=Plane.YZ)
                with BuildLine(Plane.XZ):
                    for ym in (-1, 1):
                        RadiusArc(
                            (-ww / 2, ym * tilt / 2, ym * base_size / 2),
                            (ww / 2, ym * tilt / 2, ym * base_size / 2),
                            helmet_curve_radius,
                        )
            if not ln.line:
                raise RuntimeError("Empty line")
            bottom_face = Face.make_surface(ln.edges()).move(
                Location((0, 0, tilt / 2 - bottom_thickness))
            )
            with BuildSketch(Plane.XY.offset(-bottom_thickness / 2)) as sk2:
                Rectangle(base_size, base_size)
            loft((bottom_face, sk2.sketch))
            extrude(sk2.sketch, bottom_thickness / 2)
            if ww > base_size:
                fillet(
                    p.edges(Select.LAST)
                    .filter_by(Plane.YZ)
                    .group_by(Axis.Z)[0],
                    bottom_thickness / 2,
                )
            # Outer corner fillet
            edges = p.edges().filter_by(Plane.YZ).group_by(Axis.Z)[0]
            fillet(edges, min(base_thickness * 0.9, edge_chamfer * 2))

            # Strap cutouts
            strap_z = -(bottom_thickness - strap_radius + edge_chamfer * 1.5)
            more_z = math.tan(math.radians(tilt_angle / 2)) * base_size / 2
            with Locations(
                Location((0, 0, strap_z - more_z), (tilt_angle / 2, 0, 0))
            ):
                SliderStrapGrips(
                    base_size,
                    height=StrapGripSize.width * 3.25 - edge_chamfer / 2,
                    mode=Mode.SUBTRACT,
                )
            if fancy:
                try:
                    faces = p.faces(Select.LAST)
                    faces = (
                        (
                            faces.filter_by(GeomType.BSPLINE)
                            + faces.filter_by(GeomType.CYLINDER)
                            + faces.filter_by(Plane.YZ)
                        )
                        .filter_by_position(Axis.Z, -bottom_thickness, 0)
                        .sort_by(SortBy.AREA, reverse=True)
                    )[:2]
                    edges = list(
                        faces.edges()
                        .filter_by_position(
                            Axis.Y,
                            -base_size / 2 + 0.1,
                            base_size / 2 - 0.1,
                        )
                        .filter_by_position(
                            Axis.Z, -bottom_thickness * 2, -0.1
                        )
                        .group_by(Axis.Z, reverse=True)
                    )[:4]
                    fillet(edges, edge_chamfer)
                except ValueError:
                    print("Side strap fillet failed")  # noqa: T201
                try:
                    bottom_face = (
                        p.faces().filter_by(GeomType.CYLINDER)
                        + p.faces().filter_by(GeomType.BSPLINE)
                    ).sort_by(SortBy.AREA, reverse=True)[0]
                    edges = bottom_face.edges().filter_by_position(
                        Axis.Y,
                        -StrapGripSize.length / 2,
                        StrapGripSize.length / 2,
                    )
                    fillet(edges, edge_chamfer)
                except ValueError:
                    print("Bottom strap fillet failed")  # noqa: T201

        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountBase(BasePartObject):
    def __init__(
        self,
        base_size: float,
        base_thickness: float,
        grip_thickness: float,
        slider_fit: float,
        mid_thickness: float,
        bottom_thickness: float,
        bottom_extension: float,
        screw_size: float,
        screw_chamfer: float = 1 * MM,
        edge_chamfer: float = 0.4 * MM,
        strap_radius: float = 8 * MM,
        tilt_angle: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        with BuildPart() as p:
            SliderBase(
                base_size,
                base_thickness,
                grip_thickness,
                slider_fit,
                mid_thickness,
                screw_size,
                screw_chamfer,
            )
            MountBottom(
                base_size,
                base_thickness,
                bottom_thickness,
                bottom_extension,
                edge_chamfer=edge_chamfer,
                strap_radius=strap_radius,
                tilt_angle=tilt_angle,
                fancy=fancy,
            )
            # Top outer slider channel corner fillet
            faces = (
                p.faces()
                .filter_by(GeomType.BSPLINE)
                .filter_by_position(Axis.Z, 0, mid_thickness)
                .sort_by(SortBy.AREA)
            )
            edges = (
                faces[-2:]
                .edges()
                .filter_by_position(Axis.Z, base_thickness, mid_thickness)
                .sort_by(SortBy.LENGTH, reverse=True)[:4]
                .sort_by_distance((0, 0, 0), reverse=True)[:2]
            )
            fillet(edges, min(base_thickness * 0.9, edge_chamfer * 2))

            if fancy:
                fillet(
                    first_and_last(
                        p.edges().filter_by(Plane.XZ).group_by(Axis.Y)
                    ),
                    edge_chamfer / 1,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BikeHelmetCameraMount(Model):
    print_orientation: bool = True
    base_size: float = 35
    rail_size: float = 30
    thickness: float = 10
    riser_thickness: float = 4
    screw_size: float = 5
    insert_size: float = 6.7
    bottom_thickness: float = 8
    bottom_extension: float = 20
    slider_top_thickness: float = 0.6
    slider_base_thickness: float = 0.6
    slider_grip_thickness: float = 8
    slider_fit: float = 0.2
    base_tilt_angle: float = 15
    edge_chamfer: float = 0.4
    fancy: bool = True

    @cached_property
    def mid_size(self) -> float:
        return self.base_size - self.slider_grip_thickness * 2

    @cached_property
    @PrintRotation(x=90)
    def mount(self) -> Part:
        with (
            BuildPart() as p,
            Locations(
                (0, 0, self.slider_base_thickness + self.slider_fit + 8 * MM)
            ),
        ):
            MountTop(
                self.base_size,
                self.rail_size,
                self.thickness,
                self.riser_thickness,
                self.screw_size,
                self.slider_top_thickness,
                self.slider_grip_thickness - self.slider_fit,
                edge_chamfer=self.edge_chamfer,
                fancy=self.fancy,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Mount"
        return p.part

    @cached_property
    @PrintRotation(x=90)
    def base(self) -> Part:
        with BuildPart() as p:
            MountBase(
                self.base_size,
                self.slider_base_thickness,
                self.slider_grip_thickness,
                self.slider_fit,
                self.thickness,
                self.bottom_thickness,
                self.bottom_extension,
                self.insert_size,
                edge_chamfer=self.edge_chamfer,
                tilt_angle=self.base_tilt_angle,
                fancy=self.fancy,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Base"
        p.part.color = Color(0x22CC66, 0xFF)
        return p.part

    @cached_property
    @PrintRotation(x=90)
    def rail_test_part(self) -> Part:
        with BuildPart() as p:
            with (
                BuildSketch(Plane.XZ.offset(-self.base_size / 2)),
                Locations(
                    (0, -(self.riser_thickness + self.slider_base_thickness))
                ),
            ):
                RiserProfile(
                    self.base_size,
                    self.riser_thickness,
                    self.slider_base_thickness,
                )
            extrude(amount=self.base_size)
            Rails(
                length=self.rail_size,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Rail test"
        p.part.color = Color(0x22AAEE, 0xFF)
        return p.part

    def build(self) -> Model.Geometry | None:
        return arrange(
            self.rail_test_part,
            self.mount,
            self.base,
            pack_parts=self.print_orientation,
        )
