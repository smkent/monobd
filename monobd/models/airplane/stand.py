from __future__ import annotations

from bdbox import Model
from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Mode,
    Plane,
    Polyline,
    SortBy,
    extrude,
    fillet,
    make_face,
    revolve,
)


class ModelAirplaneStand(Model):
    rod_diameter: float = 16
    rod_length: float = 60
    base_diameter: float = 16 * 4
    base_thickness: float = 4
    angle: float = 8

    def build(self) -> Model.Geometry | None:
        with BuildPart() as p:
            # Rod
            rod_plane = Plane.XY.rotated((self.angle, 0, 0))
            with BuildSketch(rod_plane):
                Circle(self.rod_diameter / 2)
            extrude(amount=self.rod_length, both=True)
            fillet(
                p.edges()
                .filter_by(rod_plane)
                .group_by(Axis(rod_plane.origin, rod_plane.z_dir))[-1],
                2,
            )
            Box(
                self.rod_length * 2,
                self.rod_length * 2,
                self.rod_length * 2,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.INTERSECT,
            )

            # Base
            with BuildSketch(Plane.YZ):
                with BuildLine():
                    arc = CenterArc(
                        (
                            self.base_diameter / 2 - self.base_thickness,
                            -self.base_thickness,
                        ),
                        radius=self.base_thickness,
                        start_angle=0,
                        arc_size=90,
                    )
                    Polyline(
                        arc @ 0, (0, (arc @ 0).Y), (0, (arc @ 1).Y), arc @ 1
                    )
                make_face()
            revolve()

            # Connection
            fillet(
                p.edges()
                .filter_by(Plane.XY)
                .group_by(Axis.Z)[1]
                .sort_by(SortBy.LENGTH)[0],
                (self.base_diameter - self.rod_diameter) / 4,
            )
        return p
