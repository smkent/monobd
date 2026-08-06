from __future__ import annotations

import math
from functools import cached_property

from bdbox import Float, Model
from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Color,
    Compound,
    CounterBoreHole,
    GeomType,
    Keep,
    Line,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polyline,
    Pos,
    RadiusArc,
    Rectangle,
    RegularPolygon,
    Rot,
    Rotation,
    RotationLike,
    Text,
    TextAlign,
    Vector,
    add,
    extrude,
    fillet,
    make_face,
    mirror,
    revolve,
    split,
)

from monobd.objects.hole import PrintableCounterBoreHole


class HornMeasurements:
    barrel_size = Vector(17.5, 17.5, 31)
    barrel_corner_radius = 6.5
    barrel_grip_space = barrel_size.Z / 2 - 4
    handlebar_round = barrel_size.Z / 2


class NutCutout(BasePartObject):
    def __init__(
        self,
        screw_size: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.SUBTRACT,
        *,
        printable_bridge: bool = False,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch() as sk:
                RegularPolygon(radius=screw_size, side_count=6, rotation=90)
            extrude(sk.sketch, amount=height)
            if printable_bridge > 0:
                with BuildSketch() as sk:
                    Rectangle(screw_size * 2, screw_size * 2)
                    Rectangle(screw_size * 2, screw_size, mode=Mode.SUBTRACT)
                extrude(sk.sketch, amount=0.4, mode=Mode.SUBTRACT)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ClampBaseProfile(BaseSketchObject):
    def __init__(
        self,
        length: float,
        width: float = HornMeasurements.barrel_grip_space,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.MIN, Align.MIN),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with BuildLine():
                arc = CenterArc(
                    (length - width / 2, width / 2),
                    radius=width / 2,
                    start_angle=90,
                    arc_size=-180,
                )
                Polyline(arc @ 0, (0, (arc @ 0).Y), (0, (arc @ 1).Y), arc @ 1)
            make_face()
            with Locations(Rotation(0, 0, 270)):
                Circle(
                    radius=HornMeasurements.handlebar_round,
                    arc_size=180,
                    align=(Align.MAX, Align.MIN),
                )
            fillet(
                sk.vertices().filter_by_position(
                    Axis.X,
                    HornMeasurements.handlebar_round / 2,
                    HornMeasurements.handlebar_round,
                ),
                HornMeasurements.handlebar_round,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class ClampBase(BasePartObject):
    def __init__(
        self,
        horn_clamp_thickness: float,
        clamp_separation: float,
        screw_size: float,
        width: float = HornMeasurements.barrel_grip_space,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        height = HornMeasurements.barrel_size.Y + horn_clamp_thickness * 2
        base_length = (
            HornMeasurements.barrel_size.X + HornMeasurements.handlebar_round
        )
        length = base_length + horn_clamp_thickness + screw_size * 2
        with BuildPart() as p:
            with BuildSketch(Plane.XY) as sk:
                ClampBaseProfile(length, width)
            extrude(sk.sketch, amount=height / 2, both=True)
            with BuildSketch(-Plane.XZ) as sk:
                Rectangle(
                    HornMeasurements.barrel_size.X
                    + HornMeasurements.handlebar_round,
                    HornMeasurements.barrel_size.Y,
                    align=(Align.MIN, Align.CENTER),
                )
                fillet(
                    sk.vertices().group_by(Axis.X)[-1],
                    HornMeasurements.barrel_corner_radius,
                )
                Rectangle(
                    length, clamp_separation, align=(Align.MIN, Align.CENTER)
                )
                fillet(
                    sk.vertices()
                    .filter_by_position(
                        Axis.X,
                        HornMeasurements.handlebar_round,
                        HornMeasurements.handlebar_round
                        + HornMeasurements.barrel_size.Y,
                    )
                    .filter_by_position(
                        Axis.Y,
                        -clamp_separation / 2 - 0.1,
                        clamp_separation / 2 + 0.1,
                    ),
                    HornMeasurements.barrel_corner_radius / 4,
                )
            extrude(
                sk.sketch,
                amount=HornMeasurements.handlebar_round * 2,
                mode=Mode.SUBTRACT,
            )
            if fancy:
                fillet(
                    p.edges()
                    .filter_by(Plane.XY)
                    .filter_by_position(Axis.X, length - screw_size, length)
                    .sort_by_distance((0, 0, 0))[:2],
                    0.2,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountBody(BasePartObject):
    def __init__(
        self,
        handlebar_radius: float,
        horn_clamp_thickness: float,
        clamp_separation: float,
        screw_size: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        with BuildPart() as p:
            ClampBase(
                horn_clamp_thickness,
                clamp_separation,
                screw_size,
                width=HornMeasurements.barrel_grip_space,
                fancy=fancy,
                rotation=(0, 0, 270),
                align=(Align.MIN, Align.CENTER, Align.CENTER),
            )
            with BuildSketch(Plane.XZ) as sk:
                Rectangle(
                    HornMeasurements.handlebar_round,
                    HornMeasurements.barrel_size.Y + horn_clamp_thickness * 2,
                    align=(Align.MIN, Align.CENTER),
                )
            revolve(sk.sketch, revolution_arc=-180)
            with BuildSketch() as sk:
                base_length = (
                    HornMeasurements.barrel_size.X
                    + HornMeasurements.handlebar_round
                )
                length = base_length + horn_clamp_thickness + screw_size * 2
                ClampBaseProfile(
                    length, align=(Align.MIN, Align.CENTER), rotation=270
                )
            extrude(
                sk.sketch,
                amount=HornMeasurements.barrel_size.Y / 2
                + horn_clamp_thickness,
                both=True,
                mode=Mode.INTERSECT,
            )
            with BuildSketch() as sk:
                Circle(radius=handlebar_radius)
            extrude(
                sk.sketch,
                amount=HornMeasurements.barrel_size.Y / 2
                + horn_clamp_thickness,
                both=True,
                mode=Mode.SUBTRACT,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountClampProfileMask(BasePartObject):
    def __init__(
        self,
        horn_clamp_thickness: float,
        handlebar_grip_size: float,
        handlebar_jaw_length: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.MIN,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        height = HornMeasurements.barrel_size.Y + horn_clamp_thickness * 2
        with BuildPart() as p:
            with BuildSketch(Plane.YZ) as sk:
                with Locations((-HornMeasurements.handlebar_round, 0)):
                    Rectangle(
                        HornMeasurements.handlebar_round * 2
                        + handlebar_jaw_length,
                        height * 2,
                        align=(Align.MIN, Align.CENTER),
                    )
                with BuildSketch(Plane.YZ, mode=Mode.SUBTRACT):
                    with BuildLine() as ln:
                        min_x = -HornMeasurements.handlebar_round
                        max_x = (
                            HornMeasurements.handlebar_round
                            + handlebar_jaw_length
                        )
                        arc = CenterArc(
                            (max_x - handlebar_grip_size, 0),
                            radius=handlebar_grip_size,
                            start_angle=270,
                            arc_size=180,
                        )
                        a0, a1 = arc @ 0, arc @ 1
                        add_x = abs(
                            min_x
                            * min(0.65, 0.4 + 0.10 * horn_clamp_thickness)
                        )
                        pts = [
                            arc @ 1,
                            (add_x, a1.Y),
                            (min_x / 2 + add_x, height / 2),
                            (min_x, height / 2),
                            (min_x, -height / 2),
                            (min_x / 2 + add_x, -height / 2),
                            (add_x, a0.Y),
                            arc @ 0,
                        ]
                        Polyline(pts)
                        fillet(
                            list(ln.vertices().group_by(Axis.X))[1:-1],
                            handlebar_grip_size * 2,
                        )
                    make_face()
            extrude(
                sk.sketch,
                amount=HornMeasurements.handlebar_round * 2 * 2,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountClamp(BasePartObject):
    def __init__(
        self,
        handlebar_radius: float,
        horn_clamp_thickness: float,
        screw_size: float,
        handlebar_grip_size: float,
        handlebar_jaw_length: float,
        handlebar_clamp_opening_angle: float = 75,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.MIN,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        height = HornMeasurements.barrel_size.Y + horn_clamp_thickness * 2
        with BuildPart() as p:
            with BuildSketch(Plane.XY.rotated((0, 0, 90))) as sk:
                with BuildLine() as ln:
                    arc = CenterArc(
                        (0, 0),
                        radius=handlebar_radius,
                        start_angle=handlebar_clamp_opening_angle / 2,
                        arc_size=(360 - handlebar_clamp_opening_angle),
                    )
                    out_r = min(
                        (
                            (arc @ 0).Y
                            + min(horn_clamp_thickness, screw_size)
                            + screw_size
                        ),
                        HornMeasurements.handlebar_round,
                    )
                    angle2 = math.degrees(
                        2 * math.asin(out_r / HornMeasurements.handlebar_round)
                    )
                    arc2 = CenterArc(
                        (0, 0),
                        radius=HornMeasurements.handlebar_round,
                        start_angle=angle2 / 2,
                        arc_size=(360 - angle2),
                    )
                    pl = Polyline(
                        arc @ 0,
                        (
                            (
                                HornMeasurements.handlebar_round
                                + handlebar_jaw_length
                            ),
                            (arc @ 0).Y,
                        ),
                        (
                            (
                                HornMeasurements.handlebar_round
                                + handlebar_jaw_length
                            ),
                            (arc2 @ 0).Y - handlebar_grip_size / 2,
                        ),
                        arc2 @ 0,
                    )
                    mirror(pl, about=Plane.XZ)
                    verts = ln.vertices().group_by(Axis.X)
                    if out_r < HornMeasurements.handlebar_round:
                        fillet(verts[1], handlebar_grip_size / 2)
                        try:
                            fillet(verts[0], HornMeasurements.handlebar_round)
                        except ValueError:
                            print("Handlebar clamp outer fillet failed")  # noqa: T201
                make_face()
            extrude(sk.sketch, amount=height / 2, both=True)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BikeHornMount(Model):
    handlebar_fit_diameter: float = Float(
        1 * IN + 2.0 * MM,
        description="Handlebar clamp diameter (in mm), including fit",
    )
    horn_clamp_thickness: float = 4.0
    handlebar_clamp_rotation: float = 10
    handlebar_clamp_extra_length: float = 0
    handlebar_clamp_opening_angle: float = Float(
        75, min=0, max=180, step=1, description="Handlebar clamp arc angle"
    )
    screw_size: float = 3
    screw_fit: float = 0.3
    fancy: bool = True

    @cached_property
    def handlebar_fit(self) -> float:
        return (
            HornMeasurements.handlebar_round - self.handlebar_fit_diameter / 2
        )

    @cached_property
    def handlebar(self) -> Part:
        with BuildPart() as p:
            with BuildSketch():
                Circle(radius=self.handlebar_fit_diameter / 2)
            extrude(amount=self.handlebar_fit_diameter * 1.5, both=True)
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Handlebar"
        p.part.color = Color(0x0066EE, 0x33)
        return p.part

    @cached_property
    def horn_body(self) -> Part:
        with BuildPart() as p:
            plane = Plane.XY.moved(
                Location(
                    (
                        HornMeasurements.handlebar_round + 8,
                        -(
                            HornMeasurements.handlebar_round
                            + HornMeasurements.barrel_size.Y
                            - 8
                        ),
                        0,
                    )
                )
            ).rotated((0, 0, 160))
            with BuildSketch(plane) as sk:
                with BuildLine() as ln:
                    l0 = Line((0, 30), (45 / 2 - 10, 30))
                    arc = RadiusArc(
                        l0 @ 1, (45 / 2, (l0 @ 1).Y - 10), radius=10
                    )
                    arc2 = RadiusArc(arc @ 1, ((45 / 2 - 10), 10), 10)
                    arc3 = RadiusArc(arc2 @ 1, (7, 0), -20)
                    fillet(ln.vertices(), 7)
                    Polyline(arc3 @ 1, (0, 0), l0 @ 0)
                make_face()
            revolve(sk.sketch, axis=Axis(plane.origin, plane.y_dir))

            with BuildSketch(
                Plane.YZ.shift_origin(
                    (
                        0,
                        -HornMeasurements.handlebar_round,
                        0,
                    )
                ).offset(-HornMeasurements.handlebar_round)
            ) as sk:
                Rectangle(
                    HornMeasurements.barrel_size.X,
                    HornMeasurements.barrel_size.Y,
                    align=(Align.MAX, Align.CENTER),
                )
                fillet(sk.vertices(), HornMeasurements.barrel_corner_radius)
            extrude(sk.sketch, amount=HornMeasurements.barrel_size.Z)
            with BuildSketch(
                Plane.XY.shift_origin((0, -HornMeasurements.handlebar_round))
            ) as sk:
                Rectangle(
                    HornMeasurements.barrel_size.Z / 2,
                    HornMeasurements.barrel_size.X / 2,
                    align=(Align.MIN, Align.MAX),
                )
            extrude(
                sk.sketch, amount=HornMeasurements.barrel_size.Y / 2, both=True
            )
            with BuildSketch(Plane.XY) as sk:
                Rectangle(
                    HornMeasurements.handlebar_round * 2,
                    (
                        HornMeasurements.handlebar_round
                        + HornMeasurements.barrel_size.X / 2
                    ),
                    align=(Align.CENTER, Align.MAX),
                )
                Circle(
                    radius=HornMeasurements.handlebar_round, mode=Mode.SUBTRACT
                )
            for keep, height in zip(
                (Keep.TOP, Keep.BOTTOM),
                (8, HornMeasurements.barrel_size.Y),
                strict=True,
            ):
                extrude(
                    split(sk.sketch, Plane.YZ, keep, mode=Mode.PRIVATE),
                    amount=height / 2,
                    both=True,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Horn body"
        p.part.color = Color(0x666666, 0xFF)
        return p.part

    @cached_property
    def mount_body(self) -> Part:
        handlebar_grip_size = self.screw_size * 2.0
        handlebar_jaw_length = (
            handlebar_grip_size
            + self.screw_size
            + self.handlebar_clamp_extra_length
        )
        horn_jaw_thickness = 2 * MM
        clamp_separation = (
            HornMeasurements.barrel_size.Y - 2 * horn_jaw_thickness
        )
        with BuildPart() as p:
            horn_mount = MountBody(
                handlebar_radius=self.handlebar_fit_diameter / 2,
                horn_clamp_thickness=self.horn_clamp_thickness,
                clamp_separation=clamp_separation,
                screw_size=self.screw_size,
                fancy=self.fancy,
            )
            clamp_rotation_axis = Axis(
                (0, 1 * HornMeasurements.handlebar_round, 0),
                Axis.Z.direction,
            )
            clamp = MountClamp(
                handlebar_radius=self.handlebar_fit_diameter / 2,
                horn_clamp_thickness=self.horn_clamp_thickness,
                screw_size=self.screw_size,
                handlebar_grip_size=handlebar_grip_size,
                handlebar_jaw_length=handlebar_jaw_length,
                handlebar_clamp_opening_angle=(
                    self.handlebar_clamp_opening_angle
                ),
                mode=Mode.PRIVATE,
            ).rotate(clamp_rotation_axis, -self.handlebar_clamp_rotation)
            clamp_mask = MountClampProfileMask(
                self.horn_clamp_thickness,
                handlebar_grip_size,
                handlebar_jaw_length,
            ).rotate(clamp_rotation_axis, -self.handlebar_clamp_rotation)

            with Locations((0, -HornMeasurements.handlebar_round, 0)):
                add(clamp)
                add(clamp_mask, mode=Mode.SUBTRACT)

            # Save faces for screw hole locations
            clamp_face = p.faces().group_by(Axis.Y)[0].sort_by(Axis.Z)[-1]
            hb_screw_face, hb_nut_face = (
                p.faces()
                .filter_by(
                    Plane.YZ.rotated((0, 0, -self.handlebar_clamp_rotation))
                )
                .sort_by_distance(
                    (
                        (
                            (
                                HornMeasurements.handlebar_round
                                + handlebar_grip_size
                            )
                            * math.tan(
                                math.radians(self.handlebar_clamp_rotation)
                            )
                        ),
                        HornMeasurements.handlebar_round + handlebar_grip_size,
                    )
                )[:2]
                .sort_by_distance((-handlebar_grip_size, 0, 0))
            )

            # Handlebar fit diameter text
            text_pos = Pos(
                -(
                    HornMeasurements.handlebar_round
                    - HornMeasurements.barrel_grip_space / 2
                ),
                -HornMeasurements.handlebar_round,
                -(
                    HornMeasurements.barrel_size.Y / 2
                    + self.horn_clamp_thickness
                ),
            ) * Rot(0, 0, 90)
            with BuildSketch(-Plane(text_pos)) as sk:
                Text(
                    f"{round(self.handlebar_fit_diameter, 1)}",
                    HornMeasurements.barrel_grip_space / 1.5,
                    text_align=(TextAlign.LEFT, TextAlign.CENTER),
                    align=(Align.MAX, Align.CENTER),
                )
            extrude(sk.sketch, amount=-0.4, mode=Mode.SUBTRACT)

            # Edge fillets
            if self.fancy:
                edge_set = (
                    p.edges()
                    .filter_by(Plane.XY)
                    .filter_by_position(
                        Axis.Y, horn_mount.bounding_box().min.Y, 0
                    )
                    .filter_by_position(
                        Axis.X, horn_mount.bounding_box().min.X, 0
                    )
                    .filter_by(GeomType.CIRCLE)
                    .group_by(Axis.Z)[-1]
                )
                outer_edge, *_, inner_edge = edge_set.group_by(Axis.Y)
                try:
                    fillet(inner_edge, self.handlebar_fit * 0.2)
                except ValueError:
                    print("Inner edge finish failed")  # noqa: T201
                try:
                    fillet(outer_edge, self.handlebar_fit * 0.2)
                except ValueError:
                    print("Outer edge finish failed")  # noqa: T201

            # Horn clamp screw/nut holes
            end_pos = clamp_face.position_at(0.5, 1)
            pos = Vector(end_pos.X, clamp_face.position_at(0, 0).Y, end_pos.Z)
            cutout_depth = min(
                (
                    horn_jaw_thickness
                    + self.horn_clamp_thickness
                    - self.screw_size
                ),
                self.screw_size,
            )
            with Locations(Plane(pos)):
                PrintableCounterBoreHole(
                    radius=(self.screw_size + self.screw_fit) / 2,
                    counter_bore_radius=self.screw_size,
                    counter_bore_depth=cutout_depth,
                )
            with Locations(-Plane((pos.X, pos.Y, -pos.Z))):
                NutCutout(
                    self.screw_size + self.screw_fit,
                    cutout_depth,
                    printable_bridge=True,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )

            # Handlebar clamp screw/nut holes
            screw_loc = Location(
                ((handlebar_jaw_length - handlebar_grip_size) / 2, 0, 0)
            )
            with Locations(
                -Plane(hb_screw_face)
                .moved(screw_loc)
                .offset(-self.screw_size * 2)
            ):
                CounterBoreHole(
                    radius=(self.screw_size + self.screw_fit) / 2,
                    counter_bore_radius=self.screw_size,
                    counter_bore_depth=self.screw_size,
                )

            with Locations(
                -Plane(hb_nut_face)
                .moved(screw_loc)
                .offset(-self.screw_size * 2)
            ):
                NutCutout(
                    self.screw_size + self.screw_fit,
                    self.screw_size * 2,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Mount body"
        return p.part

    def build(self) -> Model.Geometry | None:
        return Compound(
            children=[self.mount_body, self.horn_body, self.handlebar]
        )
