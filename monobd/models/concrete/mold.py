from __future__ import annotations

import math
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from bdbox import Choice, Model
from build123d import (
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Cone,
    Cylinder,
    Face,
    GeomType,
    Keep,
    Locations,
    Mode,
    Plane,
    Pos,
    Rectangle,
    RegularPolygon,
    Rot,
    RotationLike,
    ShapeList,
    Vector,
    add,
    chamfer,
    extrude,
    import_step,
    scale,
    split,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence


class Assets:
    DIR = Path(__file__).parent / "assets"

    PUMPKIN = DIR / "PumpkinMold.Pumpkin.step"
    PUMPKIN_60 = DIR / "Pumpkin_60mm.step"


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


class ScrewPair(BasePartObject):
    def __init__(
        self,
        screw_size: float,
        screw_length: float,
        screw_fit: float,
        height: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] | None = None,
        mode: Mode = Mode.SUBTRACT,
    ) -> None:
        with BuildPart() as p:
            nut_depth = min(screw_length / 2, screw_size)
            with Locations(Pos(0, 0, nut_depth)):
                NutCutout(
                    screw_size=screw_size + screw_fit,
                    height=nut_depth,
                    rotation=(0, 0, 90),
                    mode=Mode.ADD,
                )
            with BuildSketch():
                Circle((screw_size + screw_fit) / 2)
            extrude(amount=-screw_length, both=True)
            cone_radius = (screw_size + screw_fit) / 2
            Cone(
                bottom_radius=cone_radius * 1.5 + screw_fit / 2,
                top_radius=cone_radius * 2 + screw_fit / 2,
                height=cone_radius / 2,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )
            with (
                Locations(
                    Rot(180, 0, 0) * Pos(0, 0, screw_length),
                    Rot(0, 0, 0) * Pos(0, 0, nut_depth * 2),
                ) as bore_locs,
                BuildSketch(*bore_locs.locations),
            ):
                Circle((screw_size / 2) * 3)
            extrude(amount=height)
        if not p.part:
            raise RuntimeError("Empty part")
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ConcreteMold(Model):
    shape: str = Choice("octagon", ["round", "square", "octagon"])
    model_scale: float = 1.0
    mold_thickness: float = 6
    screw_size: float = 3
    screw_length: float = 10
    screw_fit: float = 0.3

    @cached_property
    def molded_model(self) -> Compound:
        model = import_step(Assets.PUMPKIN)
        if self.model_scale != 1:
            model = scale(model, self.model_scale)
        model.move(
            Pos(
                model.bounding_box().to_align_offset(
                    (Align.CENTER, Align.CENTER, Align.MIN)
                )
            )
        )
        model.label = "Molded Model"
        return model

    @cached_property
    def model_size(self) -> Vector:
        return self.molded_model.bounding_box().size

    @cached_property
    def mold_radius(self) -> float:
        return (
            max(self.model_size.X, self.model_size.Y) / 2 + self.mold_thickness
        )

    @contextmanager
    def cut_locations(self, cuts: Sequence[Plane]) -> Iterator[Locations]:
        space = self.screw_size * 3.125
        planes = [c.moved(Pos(0, i * -space, 0)) for i, c in enumerate(cuts)]
        with (
            Locations(Rot(0, 0, 0), Rot(0, 0, 180)),
            Locations(*planes) as locs,
        ):
            yield locs

    @contextmanager
    def screw_locations(self) -> Iterator[Locations]:
        with Locations(
            Pos(self.mold_radius * 0.35, self.screw_size * (2 + 3.125), 0),
            Pos(
                self.mold_radius - self.screw_size * 1.65,
                self.screw_size * (2 + 3.125),
                0,
            ),
            Pos(
                self.mold_radius - self.screw_size * 1.65,
                (self.model_size.Z + self.mold_thickness * 2)
                - self.screw_size * 1.45,
                0,
            ),
        ) as locs:
            yield locs

    @cached_property
    def mold_base_shape(self) -> Compound:
        with BuildPart() as p:
            with BuildSketch():
                if self.shape == "round":
                    Circle(self.mold_radius)
                elif self.shape == "octagon":
                    RegularPolygon(
                        self.mold_radius,
                        side_count=8,
                        major_radius=False,
                        rotation=360 / 8 / 2,
                    )
                else:
                    Rectangle(
                        self.model_size.X + self.mold_thickness * 2,
                        self.model_size.Y + self.mold_thickness * 2,
                    )
            extrude(amount=self.model_size.Z + self.mold_thickness * 2)
            chamfer(
                p.edges().filter_by(Plane.XY),
                min(self.mold_radius, self.model_size.Z / 2) / 16,
            )
        if not p.part:
            raise RuntimeError("Empty part")
        return p.part

    @cached_property
    def mold_sections(self) -> Compound:
        cuts = (Plane.YZ, Plane.XZ)
        with BuildPart() as p:
            add(self.mold_base_shape)
            with Locations(
                Pos(0, 0, self.mold_thickness)
                * Pos(0, 0, self.model_size.Z)
                * Rot(180, 0, 0)
            ):
                added_model = add(self.molded_model, mode=Mode.SUBTRACT)
                extrude(
                    added_model.faces()
                    .filter_by(Plane.XY)
                    .sort_by(Axis.Z)[-1],
                    amount=self.mold_thickness,
                    mode=Mode.SUBTRACT,
                )

            with self.cut_locations(cuts), self.screw_locations():
                ScrewPair(
                    screw_size=self.screw_size,
                    screw_length=self.screw_length,
                    screw_fit=self.screw_fit,
                    height=self.mold_radius,
                )
        if not p.part:
            raise RuntimeError("Empty part")
        solid = p.part.solid()
        for cut in cuts:
            solid = split(solid, bisect_by=cut, keep=Keep.BOTH)
        return Compound(label="Mold", children=solid.solids())

    @cached_property
    def mold(self) -> Compound:
        def _match_screw_hole_face(face: Face) -> bool:
            if len(edges := face.edges()) != 1:
                return False
            if (edge := edges[0]).geom_type != GeomType.CIRCLE:
                return False
            return math.isclose(
                edge.radius, (self.screw_size + self.screw_fit) / 2
            )

        def _screw_hole_faces(p: Compound) -> Iterator[ShapeList[Face]]:
            for cut_plane in cuts:
                axis = Axis(cut_plane.origin, cut_plane.z_dir)
                search_face = (
                    p.faces()
                    .filter_by(cut_plane)
                    .filter_by_position(axis, -0.1, 0.1)[0]
                )
                yield (
                    (search_face.without_holes() - search_face)
                    .faces()
                    .filter_by(GeomType.PLANE)
                    .filter_by(_match_screw_hole_face)
                )

        cuts = (Plane.YZ, Plane.XZ)
        sections = []
        for section in self.mold_sections.solids():
            with BuildPart() as p:
                add(section)
                if not p.part:
                    raise RuntimeError("Empty part")
                with Locations(*_screw_hole_faces(p.part)):
                    cone_radius = (self.screw_size + self.screw_fit) / 2
                    Cone(
                        bottom_radius=cone_radius * 2,
                        top_radius=cone_radius * 1.5,
                        height=cone_radius / 2,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                    )
                    Cylinder(
                        radius=cone_radius,
                        height=cone_radius,
                        align=(Align.CENTER, Align.CENTER, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
            sections.append(p.part)
        return Compound(label="Mold", children=sections)

    def build(self) -> Model.Geometry | None:
        return self.mold
