from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from build123d import (
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    CounterSinkHole,
    GridLocations,
    Hole,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    RotationLike,
    Select,
    chamfer,
    extrude,
    fillet,
    loft,
    make_hull,
)

from ...common import Model
from ...objects import HexagonPattern


@dataclass
class PCBGrid:
    grid_x: int = 2
    grid_y: int = 1
    grid_size: float = 32
    grid_spacing: float = 2
    screw_inset: float = 3

    @property
    def grid_size_with_spacing(self) -> float:
        return self.grid_size + self.grid_spacing

    @property
    def x(self) -> float:
        return (
            self.grid_x * self.grid_size
            + (self.grid_x - 1) * self.grid_spacing
        )

    @property
    def y(self) -> float:
        return (
            self.grid_y * self.grid_size
            + (self.grid_y - 1) * self.grid_spacing
        )

    @property
    def each_grid(self) -> GridLocations:
        return GridLocations(
            self.grid_size_with_spacing,
            self.grid_size_with_spacing,
            self.grid_x,
            self.grid_y,
        )

    @property
    def each_grid_corner(self) -> GridLocations:
        return GridLocations(
            self.grid_size_with_spacing,
            self.grid_size_with_spacing,
            self.grid_x + 1,
            self.grid_y + 1,
        )

    @property
    @contextmanager
    def each_screw(self) -> Iterator[None]:
        with (
            self.each_grid,
            GridLocations(
                self.grid_size - (self.screw_inset * 2),
                self.grid_size - (self.screw_inset * 2),
                2,
                2,
            ),
        ):
            yield

    @property
    def outer_grid_corners(self) -> GridLocations:
        return GridLocations(
            self.grid_size_with_spacing * self.grid_x,
            self.grid_size_with_spacing * self.grid_y,
            2,
            2,
        )

    @property
    def outer_screws(self) -> GridLocations:
        return GridLocations(
            self.x - (self.screw_inset * 2),
            self.y - (self.screw_inset * 2),
            2,
            2,
        )


class ScrewPylon(BasePartObject):
    def __init__(
        self,
        grid: PCBGrid,
        pylon_height: float,
        base_thickness: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        with BuildPart() as p:
            aw = 2
            bw = 3
            bottom_sz = grid.screw_inset * 4 + grid.grid_spacing + aw + bw
            top_sz = grid.screw_inset * 4 + grid.grid_spacing + aw
            radius = 3 + aw / 2
            with BuildSketch():
                RectangleRounded(bottom_sz, bottom_sz, radius)
            extrude(amount=base_thickness)
            with BuildSketch(Plane.XY.offset(base_thickness)):
                RectangleRounded(bottom_sz, bottom_sz, radius)
            with BuildSketch(Plane.XY.offset(base_thickness + pylon_height)):
                RectangleRounded(top_sz, top_sz, radius)
            loft()

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class ScrewPylons(BasePartObject):
    def __init__(
        self,
        grid: PCBGrid,
        height: float,
        border: float,
        base_thickness: float,
        pylon_height: float,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.ADD,
        depth: float | None = None,
    ):
        with BuildPart() as p:
            with grid.outer_grid_corners:
                ScrewPylon(
                    grid=grid,
                    pylon_height=pylon_height,
                    base_thickness=base_thickness,
                )

            with BuildSketch():
                RectangleRounded(
                    grid.x + border * 2,
                    grid.y + border * 2,
                    radius=3 + border / 2,
                )
            extrude(amount=height, mode=Mode.INTERSECT)

        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


class BaseCutout(BasePartObject):
    def __init__(
        self,
        grid: PCBGrid,
        thickness: float,
        rotation: RotationLike = (0, 0, 0),
        shape: str = "square",
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.MIN,
        ),
        mode: Mode = Mode.SUBTRACT,
        depth: float | None = None,
    ):
        with BuildPart() as p:
            with BuildSketch() as sk:
                if shape == "square":
                    sz = grid.grid_size - 2 * (grid.screw_inset * 2) - 1
                    curve = min(6, sz * 3 / 8)
                    RectangleRounded(sz, sz, curve)
                elif shape == "cross":
                    curve = grid.grid_size / 2
                    sz = grid.grid_size * (5 / 16)
                    Rectangle(sz + curve, sz)
                    Rectangle(sz, sz + curve)
                    fillet(sk.vertices(), radius=curve / 4)
                else:
                    raise Exception(f'Unknown shape "{shape}"')
            extrude(amount=thickness)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )


@dataclass
class ESP3DP(Model, PCBGrid, name="esp-3dp"):
    screw_hole_d: float = 4.5
    base_thickness: float = 2.6
    pylon_height: float = 6
    border: float = 1.0
    mounting_screw_hole_d: float = 4.5
    edge_chamfer: float = 0.8
    base_style: str = "hex"

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "default": {},
        }

    @property
    def height(self) -> float:
        return self.base_thickness + self.pylon_height

    @property
    def mounting_screw_locations(self) -> GridLocations:
        return GridLocations(
            self.x + self.border * 2 + self.mounting_screw_hole_d * 2, 0, 2, 1
        )

    def apply_base_style(self) -> float:
        if self.base_style == "hex":
            with BuildSketch() as sk:
                HexagonPattern(
                    self.x - self.edge_chamfer * 4,
                    self.y - self.edge_chamfer * 4,
                    hex_size=6,
                    hex_spacing=1.2,
                )
                with self.outer_grid_corners:
                    sz = self.screw_inset * 4 + self.grid_spacing + 5 + 2
                    RectangleRounded(sz, sz, radius=5, mode=Mode.SUBTRACT)
            extrude(sk.sketch, amount=self.base_thickness, mode=Mode.SUBTRACT)
            return self.edge_chamfer / 2
        elif self.base_style == "grid":
            with self.each_grid:
                BaseCutout(
                    grid=self,
                    thickness=self.base_thickness,
                    shape="square",
                )
            return self.edge_chamfer
        raise Exception(f"Unknown base style {self.base_style}")

    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            with BuildSketch():
                RectangleRounded(
                    self.x + self.border * 2,
                    self.y + self.border * 2,
                    radius=3 + self.border / 2,
                )
                with self.mounting_screw_locations:
                    Circle(radius=(self.mounting_screw_hole_d / 2) * 3)
                make_hull()
            extrude(amount=self.base_thickness)
            chamfer(
                p.edges().filter_by(Plane.XY).group_by(Axis.Z)[-1],
                self.edge_chamfer,
            )
            ScrewPylons(
                grid=self,
                border=self.border,
                height=self.height,
                base_thickness=self.base_thickness,
                pylon_height=self.pylon_height,
            )
            chamfer(
                p.edges().filter_by(Plane.XY).group_by(Axis.Z)[-1],
                self.edge_chamfer / 2,
            )
            chamfer(
                p.edges().filter_by(Plane.XY).group_by(Axis.Z)[0],
                self.edge_chamfer,
            )
            if base_edge_chamfer := self.apply_base_style():
                chamfer(
                    p.edges(Select.LAST).filter_by(Plane.XY), base_edge_chamfer
                )
            with self.outer_screws, Locations((0, 0, self.height)):
                Hole(self.screw_hole_d / 2)
                chamfer(p.edges(Select.LAST), self.edge_chamfer)
            with (
                self.mounting_screw_locations,
                Locations((0, 0, self.base_thickness)),
            ):
                CounterSinkHole(
                    self.mounting_screw_hole_d / 2, self.mounting_screw_hole_d
                )

        p.part.label = "base"
        p.part.color = Color(0x00FF22, alpha=0x99)
        return Compound(label=self.model_name, children=[p.part])
