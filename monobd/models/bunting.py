from __future__ import annotations

from operator import itemgetter

from bdbox import Model, Preset
from build123d import (
    IN,
    MM,
    Align,
    Axis,
    BasePartObject,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Color,
    Compound,
    Cone,
    Cylinder,
    Ellipse,
    GeomType,
    JernArc,
    Line,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Select,
    chamfer,
    extrude,
    fillet,
    scale,
    sweep,
)

first_and_last = itemgetter(0, -1)

OUTER_DIAMETER = 1.9 * IN
INNER_DIAMETER = 1.59 * IN
CAP_LEN = 2 * IN
CAP_BASE_THICK = 3 * MM
CAP_ADD_D = (1 / 4 - 1 / 32) * IN
EDGE_LEN = 1 * MM
PIPE_FIT = 1 * MM
FIT = 0.5 * MM

END_THICK = 1 / 4 * IN

COUPLING_LENGTH = 2.7 * IN
COUPLING_OUTER_DIAMETER = 2.215 * IN
COUPLING_OVERLAP_LENGTH = 1.3 * IN

SCREW_NUT_DIAMETER = (1 + 1 / 8) * IN
SCREW_NUT_HEIGHT = 3.5 * MM + (0.15 * IN) - 0.2 * MM
SCREW_SQUARE_INSERT_THICKNESS = 3.5 * MM
SCREW_NUT_FIT = 0.4 * MM


class Pipe(BasePartObject):
    def __init__(
        self,
        outer_diameter: float,
        inner_diameter: float,
        length: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        out_d = outer_diameter
        in_d = inner_diameter

        with BuildPart() as p:
            with BuildSketch() as sk:
                Circle(out_d / 2)
                Circle(in_d / 2, mode=Mode.SUBTRACT)
            extrude(sk.sketch, length)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class CapLoop(BasePartObject):
    def __init__(
        self,
        angle: float = 180,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.MIN,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        cap_len = CAP_LEN
        cap_base_thick = CAP_BASE_THICK
        edge_len = EDGE_LEN

        with BuildPart() as p:
            grip_len = cap_len / 2 + cap_base_thick / 2 - edge_len * 2

            with BuildSketch(Plane.YZ):
                if angle == 180:
                    with Locations((0, (1 / 8 * IN))):
                        Ellipse(1 / 4 * IN, 1 / 8 * IN)
                    with BuildLine(Plane.XZ) as ln:
                        CenterArc(
                            (0, grip_len),
                            grip_len - 1 / 8 * IN,
                            -90,
                            angle,
                        )
                        scale(by=(0.5, 1.0, 1.0))
                else:
                    with Locations((0, (1 / 8 * IN))):
                        Ellipse(1 / 4 * IN, 1 / 8 * IN)
                    with BuildLine(Plane.XZ) as ln:
                        arc = JernArc(
                            start=(0, 0),
                            tangent=(1, 0),
                            radius=grip_len,
                            arc_size=90,
                        )
                        Line(
                            arc @ 1,
                            (
                                (arc @ 1).X,
                                cap_len + cap_base_thick - edge_len * 2,
                            ),
                        )
                        scale(by=(0.47, 1.0, 1.0))
            sweep(path=ln)  # ty: ignore[invalid-argument-type]
            if angle != 180:
                chamfer(p.edges().group_by(Axis.Z)[-1], edge_len)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class PVCCoupling(BasePartObject):
    def __init__(
        self,
        outer_diameter: float,
        coupling_outer_diameter: float,
        coupling_length: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
    ) -> None:
        out_d = outer_diameter
        coupling_out_d = coupling_outer_diameter
        coupling_overlap_length = COUPLING_OVERLAP_LENGTH

        with BuildPart() as p:
            with BuildSketch() as sk:
                Circle(coupling_out_d / 2)
                Circle((out_d - (1 / 10 * IN)) / 2, mode=Mode.SUBTRACT)
                # Circle(out_d / 2, mode=Mode.SUBTRACT)  # noqa: ERA001
            extrude(sk.sketch, coupling_length)
            with BuildSketch(
                Plane.XY, Plane.XY.offset(coupling_length).reverse()
            ) as sk:
                Circle(out_d / 2)
            extrude(sk.sketch, coupling_overlap_length, mode=Mode.SUBTRACT)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BuntingPoles(Model):
    outer_diameter_in = 1.9
    inner_diameter_in = 1.59
    coupling_length_in = 2.7
    coupling_outer_diameter_in = 2.215

    cap_add_d_in: float = 1 / 4 - 1 / 32
    end_thick_in: float = 1 / 4
    jig_fit: float = 1 / 3
    jig_interior: bool = True

    presets = (
        Preset(
            "1.5inch_pvc",
            outer_diameter_in=1.9,
            inner_diameter_in=1.59,
            coupling_length_in=2.7,
            coupling_outer_diameter_in=2.215,
            cap_add_d_in=(1 / 4 - 1 / 32),
            end_thick_in=1 / 4,
            jig_fit=1 / 3,
            jig_interior=True,
        ),
        Preset(
            "2inch_pvc",
            outer_diameter_in=2.375,
            inner_diameter_in=2.067,
            coupling_length_in=2.87,
            coupling_outer_diameter_in=2.71,
            cap_add_d_in=1 / 4,
            end_thick_in=1 / 8,
            jig_fit=0.25,
            jig_interior=False,
        ),
    )

    def build(self) -> Model.Build:
        cap = self.top_cap()
        cap.color = Color(0xEEEEEE, 0xFF)
        cap.label = "Cap"
        screw_head = self.screw_head().move(Location((4 * IN, 0, 0)))
        screw_head.color = Color(0x22FF88, 0xFF)
        screw_head.label = "ScrewHead"
        coupling_jig = self.coupling_jig().move(Location((-4 * IN, 0, 0)))
        coupling_jig.color = Color(0x2288FF, 0xFF)
        coupling_jig.label = "CouplingJig"
        return Compound(children=[cap, screw_head, coupling_jig])

    def screw_head(self) -> Part:
        diameter = SCREW_NUT_DIAMETER
        height = SCREW_NUT_HEIGHT
        square_thick = SCREW_SQUARE_INSERT_THICKNESS
        fit = SCREW_NUT_FIT
        with BuildPart() as p:
            with BuildSketch() as sk:
                Circle(diameter / 2)
                with PolarLocations(diameter / 2 + 1 / 16 * IN, 8):
                    Circle(1 / 8 * IN, mode=Mode.SUBTRACT)
                fillet(sk.vertices(), 2 * MM)
            extrude(sk.sketch, height)
            with Locations((0, 0, height - (0.3 * IN) / 2)):
                PVCCoupling(
                    outer_diameter=self.outer_diameter_in * IN,
                    coupling_outer_diameter=(
                        self.coupling_outer_diameter_in * IN
                    ),
                    coupling_length=self.coupling_length_in * IN,
                    rotation=(90, 0, 0),
                    align=(Align.CENTER, Align.MIN, Align.CENTER),
                    mode=Mode.SUBTRACT,
                )
            chamfer(list(p.edges().group_by(Axis.Z)), 1 * MM)
            with BuildSketch() as sk:
                Circle((1 / 4 * IN + fit) / 2)
            extrude(sk.sketch, height, mode=Mode.SUBTRACT)
            with BuildSketch() as sk:
                RectangleRounded(
                    (1 / 4) * IN + fit,
                    (1 / 4) * IN + fit,
                    fit,
                )
            extrude(sk.sketch, square_thick, mode=Mode.SUBTRACT)
            chamfer(p.edges(Select.LAST).group_by(Axis.Z)[0], 1 * MM)

        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "thumb_screw"
        p.part.color = Color(0x88FF22, 0x99)
        return p.part

    def top_cap(self) -> Part:
        cap_len = CAP_LEN
        cap_base_thick = CAP_BASE_THICK
        cap_add_d = self.cap_add_d_in * IN
        edge_len = EDGE_LEN
        out_d = self.outer_diameter_in * IN
        in_d = self.inner_diameter_in * IN
        pipe_fit = PIPE_FIT
        fit = FIT
        screw_hole_count = 3

        with BuildPart() as p:
            # Base
            with BuildSketch() as sk:
                Circle((out_d + cap_add_d) / 2)
            extrude(sk.sketch, cap_base_thick)
            # Interior cutout
            with BuildSketch(Plane.XY.offset(cap_base_thick)) as sk:
                Circle((out_d + cap_add_d) / 2)
                Circle((in_d - cap_add_d) / 2, mode=Mode.SUBTRACT)
            extrude(sk.sketch, cap_len)
            # Grip cutout
            with (
                BuildPart(mode=Mode.SUBTRACT),
                Locations((0, 0, cap_base_thick)),
            ):
                Cone(
                    (out_d - 0 * pipe_fit / 10) / 2,
                    (out_d + pipe_fit) / 2,
                    cap_base_thick + cap_len,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
                # Interior grip
                if False:
                    Cone(
                        (in_d + 0 * pipe_fit / 10) / 2,
                        (in_d - pipe_fit) / 2,
                        cap_base_thick + cap_len,
                        align=[Align.CENTER, Align.CENTER, Align.MIN],
                        mode=Mode.SUBTRACT,
                    )
            chamfer(list(p.edges().group_by(Axis.Z)), edge_len)
            # Center cutout pattern
            with BuildSketch() as sk:
                wd = 1 / 4 * IN
                with Locations([(wd * i, 0, 0) for i in range(-5, 5)]):
                    Rectangle(wd / 2, out_d * 2)
                Circle((in_d - cap_add_d) / 2 - edge_len, mode=Mode.INTERSECT)
            extrude(sk.sketch, cap_base_thick, mode=Mode.SUBTRACT)
            # Attachment loops
            edges = []
            locs = PolarLocations(
                (out_d + cap_add_d) / 2 - 1 * MM, 6
            ).local_locations
            with Locations((0, 0, edge_len * 2)):
                with Locations(locs[1:3] + locs[4:6]):
                    CapLoop()
                edges += p.edges(Select.LAST).filter_by(GeomType.BSPLINE)
                with (
                    PolarLocations((out_d + cap_add_d) / 2 - 1 * MM, 2),
                    Locations((0, 0, cap_len - edge_len)),
                ):
                    CapLoop(
                        angle=165,
                        rotation=(180, 0, 0),
                        align=(Align.MIN, Align.CENTER, Align.MIN),
                    )
                last_edges = p.edges(Select.LAST)
                edges += last_edges.filter_by(
                    GeomType.BSPLINE
                ).filter_by_position(Axis.Z, edge_len * 1.5, 1000 * IN)
            # Attachment loop fillets
            fillet(edges, edge_len)
            # Screw holes
            with BuildPart(mode=Mode.SUBTRACT):
                ht = cap_len + cap_base_thick
                with (
                    PolarLocations(
                        (out_d + cap_add_d) / 2 - 1 * MM,
                        3,
                        start_angle=30,
                        angular_range=180,
                    ),
                    Locations(
                        [
                            (0, 0, ht * float(i) / (screw_hole_count + 1))
                            for i in range(1, screw_hole_count + 1)
                        ]
                    ),
                ):
                    Cylinder(
                        (1 / 4 * IN + fit) / 2,
                        out_d * 4,
                        rotation=(0, 270, 0),
                        align=(
                            Align.CENTER,
                            Align.CENTER,
                            Align.CENTER,
                        ),
                    )
        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "Cap"
        p.part.color = Color(0x2288FF, 0x99)
        return p.part

    def coupling_jig(self) -> Part:
        end_thick = self.end_thick_in * IN
        out_d = self.outer_diameter_in * IN
        coupling_out_d = self.coupling_outer_diameter_in * IN
        coupling_overlap_length = COUPLING_OVERLAP_LENGTH
        edge_len = EDGE_LEN

        with BuildPart() as p:
            extra = (0.1 * IN) + ((1 / 16 + 1 / 8) * IN)
            with BuildSketch() as sk:
                RectangleRounded(
                    coupling_out_d + extra,
                    coupling_out_d + extra,
                    coupling_out_d / 8,
                )
            extrude(sk.sketch, coupling_overlap_length + end_thick)
            with BuildPart(mode=Mode.SUBTRACT):
                with BuildSketch(Plane.XY.offset(end_thick)) as sk:
                    fit = 0.5 * MM
                    RectangleRounded(
                        (coupling_out_d + fit),
                        (coupling_out_d + fit),
                        coupling_out_d / 3,
                    )
                    if self.jig_interior:
                        Circle((out_d - fit) / 2, mode=Mode.SUBTRACT)
                extrude(sk.sketch, coupling_overlap_length)
                with BuildSketch() as sk:
                    Circle((out_d - fit) * self.jig_fit)
                extrude(sk.sketch, coupling_overlap_length + end_thick)
            if self.jig_interior:
                edges = first_and_last(p.edges().group_by(Axis.Z))
            else:
                edges = list(p.edges().group_by(Axis.Z))
            chamfer(edges, edge_len)
            faces = [
                Plane(p.faces().group_by(Axis.X)[0][0]).reverse(),
                Plane(p.faces().group_by(Axis.Y)[-1][0]).reverse(),
            ]
            with (
                BuildPart(faces, mode=Mode.SUBTRACT),  # ty: ignore[invalid-argument-type]
                Locations((0, end_thick / 2, 0)),
            ):
                Cylinder(
                    (1 / 4 * IN) / 2,
                    coupling_out_d * 2,
                    rotation=(0, 0, 0),
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
        if not p.part:
            raise RuntimeError("Empty part")
        return p.part
