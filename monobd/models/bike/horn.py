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
    RadiusArc,
    Rectangle,
    RegularPolygon,
    Rotation,
    RotationLike,
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


class Constants:
    handlebar_round = 15
    handlebar_radius = 1 / 2 * IN + 0.2 * MM
    handlebar_fit = handlebar_round - handlebar_radius

    barrel_handlebar_offset = 0

    barrel_size = Vector(17.5, 17.5, handlebar_round * 2)
    barrel_radius = 6.5

    barrel_grip_shorten = 4
    barrel_grip_length = barrel_size.Z / 2 - barrel_grip_shorten


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
        width: float = Constants.barrel_grip_length,
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
                    radius=Constants.handlebar_round,
                    arc_size=180,
                    align=(Align.MAX, Align.MIN),
                )
            fillet(
                sk.vertices().filter_by_position(
                    Axis.X,
                    Constants.handlebar_round / 2,
                    Constants.handlebar_round,
                ),
                Constants.handlebar_round,
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class ClampBase(BasePartObject):
    def __init__(
        self,
        clamp_thickness: float,
        screw_size: float,
        width: float = Constants.barrel_grip_length,
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
        height = Constants.barrel_size.Y + clamp_thickness * 2
        clamp_separation = Constants.barrel_size.Y - screw_size * 2
        base_length = Constants.barrel_size.X + Constants.handlebar_round
        length = base_length + clamp_thickness + screw_size * 2
        with BuildPart() as p:
            with BuildSketch(Plane.XY) as sk:
                ClampBaseProfile(length, width)
            extrude(sk.sketch, amount=height / 2, both=True)
            with BuildSketch(-Plane.XZ) as sk:
                Rectangle(
                    Constants.barrel_size.X + Constants.handlebar_round,
                    Constants.barrel_size.Y,
                    align=(Align.MIN, Align.CENTER),
                )
                fillet(
                    sk.vertices().group_by(Axis.X)[-1], Constants.barrel_radius
                )
                Rectangle(
                    length, clamp_separation, align=(Align.MIN, Align.CENTER)
                )
                fillet(
                    sk.vertices()
                    .filter_by_position(
                        Axis.X,
                        Constants.handlebar_round,
                        Constants.handlebar_round + Constants.barrel_size.Y,
                    )
                    .filter_by_position(
                        Axis.Y,
                        -clamp_separation / 2 - 0.1,
                        clamp_separation / 2 + 0.1,
                    ),
                    Constants.barrel_radius / 4,
                )
            extrude(
                sk.sketch,
                amount=Constants.handlebar_round * 2,
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
        clamp_thickness: float,
        screw_size: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
        *,
        fancy: bool = True,
    ) -> None:
        sm_width = Constants.barrel_size.Z / 2 - Constants.barrel_grip_shorten
        with BuildPart() as p:
            ClampBase(
                clamp_thickness,
                screw_size,
                width=sm_width,
                fancy=fancy,
                rotation=(0, 0, 270),
                align=(Align.MIN, Align.CENTER, Align.CENTER),
            )
            with BuildSketch(Plane.XZ) as sk:
                Rectangle(
                    Constants.handlebar_round,
                    Constants.barrel_size.Y + clamp_thickness * 2,
                    align=(Align.MIN, Align.CENTER),
                )
            revolve(sk.sketch, revolution_arc=-180)
            with BuildSketch() as sk:
                base_length = (
                    Constants.barrel_size.X + Constants.handlebar_round
                )
                length = base_length + clamp_thickness + screw_size * 2
                ClampBaseProfile(
                    length, align=(Align.MIN, Align.CENTER), rotation=270
                )
            extrude(
                sk.sketch,
                amount=Constants.barrel_size.Y / 2 + clamp_thickness,
                both=True,
                mode=Mode.INTERSECT,
            )
            with BuildSketch() as sk:
                Circle(radius=Constants.handlebar_radius)
            extrude(
                sk.sketch,
                amount=Constants.barrel_size.Y / 2 + clamp_thickness,
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
        clamp_thickness: float,
        grip_size: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.MIN,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        height = Constants.barrel_size.Y + clamp_thickness * 2
        with BuildPart() as p:
            with BuildSketch(Plane.YZ) as sk:
                with Locations((-Constants.handlebar_round, 0)):
                    Rectangle(
                        2 * Constants.handlebar_round + grip_size,
                        height * 2,
                        align=(Align.MIN, Align.CENTER),
                    )
                with BuildSketch(Plane.YZ, mode=Mode.SUBTRACT):
                    with BuildLine() as ln:
                        min_x = -Constants.handlebar_round
                        max_x = Constants.handlebar_round + grip_size
                        arc = CenterArc(
                            (max_x - grip_size, 0),
                            radius=grip_size,
                            start_angle=270,
                            arc_size=180,
                        )
                        a0, a1 = arc @ 0, arc @ 1
                        add_x = abs(min_x * 0.45)
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
                            grip_size * 2,
                        )
                    make_face()
            extrude(
                sk.sketch,
                amount=Constants.handlebar_round * 2 * 2,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class MountClamp(BasePartObject):
    def __init__(
        self,
        clamp_thickness: float,
        screw_size: float,
        grip_size: float,
        cutout_angle: float = 75,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.MIN,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        height = Constants.barrel_size.Y + clamp_thickness * 2
        with BuildPart() as p:
            with BuildSketch(Plane.XY.rotated((0, 0, 90))) as sk:
                with BuildLine() as ln:
                    arc = CenterArc(
                        (0, 0),
                        radius=Constants.handlebar_radius,
                        start_angle=cutout_angle / 2,
                        arc_size=(360 - cutout_angle),
                    )
                    out_r = min(
                        ((arc @ 0).Y + clamp_thickness + screw_size),
                        Constants.handlebar_round,
                    )
                    angle2 = math.degrees(
                        2 * math.asin(out_r / Constants.handlebar_round)
                    )
                    arc2 = CenterArc(
                        (0, 0),
                        radius=Constants.handlebar_round,
                        start_angle=angle2 / 2,
                        arc_size=(360 - angle2),
                    )
                    pl = Polyline(
                        arc @ 0,
                        (
                            Constants.handlebar_round + grip_size,
                            (arc @ 0).Y,
                        ),
                        (
                            Constants.handlebar_round + grip_size,
                            (arc2 @ 0).Y - grip_size / 2,
                        ),
                        arc2 @ 0,
                    )
                    mirror(pl, about=Plane.XZ)
                    verts = ln.vertices().group_by(Axis.X)
                    if out_r < Constants.handlebar_round:
                        fillet(verts[0], Constants.handlebar_round)
                        fillet(verts[1], grip_size / 4)
                make_face()
            extrude(sk.sketch, amount=height / 2, both=True)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BikeHornMount(Model):
    clamp_thickness: float = 2.0
    clamp_rotation: float = 20
    zip_tie_depth: float = 1
    screw_size: float = 3
    screw_fit: float = 0.4
    cutout_angle: float = Float(
        60, min=0, max=180, step=1, description="Handlebar clamp arc angle"
    )
    fancy: bool = True

    @cached_property
    def handlebar(self) -> Part:
        with BuildPart() as p:
            with BuildSketch():
                Circle(radius=Constants.handlebar_radius)
            extrude(amount=Constants.handlebar_radius * 5 / 2, both=True)
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
                        (
                            Constants.handlebar_round
                            + Constants.barrel_handlebar_offset
                            + 8
                        ),
                        -(
                            Constants.handlebar_round
                            + Constants.barrel_size.Y
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
                        -Constants.handlebar_round,
                        0,
                    )
                ).offset(
                    -Constants.handlebar_round
                    + Constants.barrel_handlebar_offset
                )
            ) as sk:
                Rectangle(
                    Constants.barrel_size.X,
                    Constants.barrel_size.Y,
                    align=(Align.MAX, Align.CENTER),
                )
                fillet(sk.vertices(), Constants.barrel_radius)
            extrude(sk.sketch, amount=Constants.barrel_size.Z)
            with BuildSketch(
                Plane.XY.shift_origin((0, -Constants.handlebar_round))
            ) as sk:
                Rectangle(
                    Constants.barrel_size.Z / 2,
                    Constants.barrel_size.X / 2,
                    align=(Align.MIN, Align.MAX),
                )
            extrude(sk.sketch, amount=Constants.barrel_size.Y / 2, both=True)
            with BuildSketch(Plane.XY) as sk:
                Rectangle(
                    (
                        Constants.handlebar_round * 2
                        + Constants.barrel_handlebar_offset
                    ),
                    Constants.handlebar_round + Constants.barrel_size.X / 2,
                    align=(Align.CENTER, Align.MAX),
                )
                Circle(radius=Constants.handlebar_round, mode=Mode.SUBTRACT)
            for keep, height in zip(
                (Keep.TOP, Keep.BOTTOM),
                (8, Constants.barrel_size.Y),
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
        grip_size = self.screw_size * 1.75
        with BuildPart() as p:
            horn_mount = MountBody(
                self.clamp_thickness, self.screw_size, fancy=self.fancy
            )
            clamp_rotation_axis = Axis(
                (0, 1 * Constants.handlebar_round, 0),
                Axis.Z.direction,
            )
            clamp = MountClamp(
                self.clamp_thickness,
                screw_size=self.screw_size,
                grip_size=grip_size,
                cutout_angle=self.cutout_angle,
                mode=Mode.PRIVATE,
            ).rotate(clamp_rotation_axis, -self.clamp_rotation)
            clamp_mask = MountClampProfileMask(
                self.clamp_thickness, grip_size
            ).rotate(clamp_rotation_axis, -self.clamp_rotation)

            with Locations((0, -Constants.handlebar_round, 0)):
                add(clamp)
                add(clamp_mask, mode=Mode.SUBTRACT)

            # Save faces for screw hole locations
            clamp_face = p.faces().group_by(Axis.Y)[0].sort_by(Axis.Z)[-1]
            hb_screw_face, hb_nut_face = (
                p.faces()
                .filter_by(Plane.YZ.rotated((0, 0, -self.clamp_rotation)))
                .sort_by_distance(
                    (0, Constants.handlebar_round + grip_size, 0)
                )[:2]
                .sort_by_distance((-grip_size, 0, 0))
            )

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
                fillet(inner_edge, Constants.handlebar_fit * 0.4)
                fillet(outer_edge, Constants.handlebar_fit * 0.4)

            # Horn clamp screw/nut holes
            end_pos = clamp_face.position_at(0.5, 1)
            pos = Vector(end_pos.X, clamp_face.position_at(0, 0).Y, end_pos.Z)
            with Locations(Plane(pos)):
                PrintableCounterBoreHole(
                    radius=(self.screw_size + self.screw_fit) / 2,
                    counter_bore_radius=self.screw_size,
                    counter_bore_depth=self.screw_size,
                )
            with Locations(-Plane((pos.X, pos.Y, -pos.Z))):
                NutCutout(
                    self.screw_size + self.screw_fit,
                    self.screw_size,
                    printable_bridge=True,
                    align=(Align.CENTER, Align.CENTER, Align.MAX),
                )

            # Handlebar clamp screw/nut holes
            with Locations(
                -Plane(hb_screw_face).offset(-(self.screw_size + 2))
            ):
                CounterBoreHole(
                    radius=(self.screw_size + self.screw_fit) / 2,
                    counter_bore_radius=self.screw_size,
                    counter_bore_depth=self.screw_size,
                )

            with Locations(-Plane(hb_nut_face).offset(-(self.screw_size + 2))):
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
