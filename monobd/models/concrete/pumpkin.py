from __future__ import annotations

from bdbox import Model
from build123d import (
    Align,
    Axis,
    BasePartObject,
    BaseSketchObject,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    EllipticalCenterArc,
    Line,
    Locations,
    Mode,
    Plane,
    PolarLocations,
    Polyline,
    Pos,
    Rectangle,
    Rot,
    RotationLike,
    SortBy,
    Triangle,
    Vector,
    VectorLike,
    extrude,
    fillet,
    make_face,
    revolve,
    sweep,
)


class EllipsoidProfile(BaseSketchObject):
    def __init__(
        self,
        x_radius: float,
        y_radius: float,
        center: VectorLike = (0, 0),
        trim_height: float | None = None,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.MIN, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        center = Vector(*center)
        out_h = trim_height if trim_height is not None else y_radius * 2
        with BuildSketch() as sk:
            with BuildLine():
                arc = EllipticalCenterArc(
                    center=(
                        center.X,
                        center.Y - (y_radius - out_h),
                    ),
                    x_radius=x_radius,
                    y_radius=y_radius,
                    start_angle=270,
                    arc_size=180,
                )
                Polyline(arc @ 0, (0, 0), arc @ 1)
            make_face()
            if trim_height is not None:
                Rectangle(
                    x_radius,
                    y_radius * 2,
                    mode=Mode.INTERSECT,
                    align=(Align.MIN, Align.MIN),
                )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class Ellipsoid(BasePartObject):
    def __init__(
        self,
        x_radius: float,
        y_radius: float,
        center: VectorLike = (0, 0),
        trim_height: float | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            with BuildSketch(Plane.XZ):
                EllipsoidProfile(
                    x_radius=x_radius,
                    y_radius=y_radius,
                    center=center,
                    trim_height=trim_height,
                )
            revolve()
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class PumpkinBody(BasePartObject):
    def __init__(
        self,
        height: float,
        trim_height: float | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        with (
            BuildPart() as p,
            PolarLocations(radius=height / 2 * 0.5, count=8),
        ):
            Ellipsoid(
                x_radius=(height / 2) * 0.75,
                y_radius=(height / 2) * 1.0,
                trim_height=trim_height,
                rotation=(0, 0, 180),
            )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class PumpkinStemProfile(BaseSketchObject):
    def __init__(
        self,
        radius: float,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            count = 8
            with PolarLocations(radius=0, count=int(count / 2)):
                Triangle(
                    a=radius * 0.75,
                    b=radius,
                    c=radius,
                    rotation=270,
                    align=(Align.CENTER, Align.MIN),
                )
                with Locations(Rot(0, 0, 360 / count)):
                    Triangle(
                        a=radius * 0.50,
                        b=radius * 1.0,
                        c=radius * 1.0,
                        rotation=270,
                        align=(Align.CENTER, Align.MIN),
                    )

            fillet(
                sk.vertices().sort_by(SortBy.DISTANCE)[:count],
                radius / (count * 1.0),
            )
            fillet(
                sk.vertices().sort_by(SortBy.DISTANCE)[-count:],
                radius / (count * 1.5),
            )
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )


class PumpkinStem(BasePartObject):
    def __init__(
        self,
        stem_radius: float,
        stem_curve_angle: float = 45,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ) -> None:
        base_depth = stem_radius
        with BuildPart() as p:
            with BuildLine(Plane.XZ) as ln:
                arc_radius = stem_radius * 2
                arc = CenterArc(
                    (arc_radius, base_depth),
                    radius=arc_radius,
                    start_angle=180,
                    arc_size=-stem_curve_angle,
                )
                l0 = Line((0, 0), arc @ 0)
            if not ln.line:
                raise RuntimeError("Empty line")
            with BuildSketch(l0 ^ 0):
                PumpkinStemProfile(radius=stem_radius * 3)
            segments = 5
            for i in range(segments + 1):
                with BuildSketch(arc ^ (i / segments)):
                    PumpkinStemProfile(
                        radius=stem_radius * (1 - (i / (segments + 1)) * 0.5)
                    )
            sweep(multisection=True)
            extrude(p.faces().sort_by(Axis.Z)[0], base_depth)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class Pumpkin(BasePartObject):
    def __init__(
        self,
        height: float,
        stem_curve_angle: float,
        bottom_trim: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildPart() as p:
            stem_radius = height / 8
            with Locations(Pos(0, 0, height / 2 - stem_radius / 2)):
                PumpkinStem(
                    stem_radius=stem_radius,
                    stem_curve_angle=stem_curve_angle,
                )
            PumpkinBody(height=height)
            if bottom_trim > 0:
                with Locations((0, 0, -height / 2 + bottom_trim)):
                    Box(
                        height * 2,
                        height * 2,
                        height * 2,
                        align=(Align.CENTER, Align.CENTER, Align.MAX),
                        mode=Mode.SUBTRACT,
                    )
                extrude(
                    -p.faces().sort_by(Axis.Z)[0].without_holes(),
                    amount=height / 2,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )
        p.part.label = "Pumpkin"


class PumpkinMold(Model):
    height: float = 100
    stem_curve_angle: float = 45

    def build(self) -> Model.Geometry | None:
        return Pumpkin(
            height=self.height,
            stem_curve_angle=self.stem_curve_angle,
            bottom_trim=self.height / 24,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
