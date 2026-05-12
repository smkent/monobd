from __future__ import annotations

from bdbox import Model
from build123d import (
    IN,
    MM,
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Locations,
    Mode,
    Rectangle,
    RectangleRounded,
    extrude,
    fillet,
)


class RouterJig(Model):
    length_in: float = 6
    width_in: float = 6
    corner_radius_in: float = 1
    thickness_mm: float = 4

    def build(self) -> Compound:
        length = self.length_in * IN
        width = self.width_in * IN
        corner_radius = self.corner_radius_in * IN
        thickness = self.thickness_mm * MM
        with BuildPart() as p:
            with BuildSketch() as sk:
                Rectangle(length, width, align=(Align.MIN, Align.MIN))
                fillet(
                    sk.vertices().sort_by_distance((0, 0))[0],
                    radius=corner_radius,
                )
                pos = (2 * IN,) * 2
                with Locations(pos):
                    Rectangle(
                        length,
                        width,
                        align=(Align.MIN, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
                    fillet(
                        sk.vertices().sort_by_distance(pos)[0],
                        radius=corner_radius / 2,
                    )
                fillet(
                    sk.vertices().sort_by_distance((length, 0))[:2],
                    radius=(1 / 4) * IN,
                )
                fillet(
                    sk.vertices().sort_by_distance((0, width))[:2],
                    radius=(1 / 4) * IN,
                )
                with Locations((pos[0] + (length - pos[0]) / 2, pos[1] / 2)):
                    RectangleRounded(
                        (length - pos[0] / 2) / 2,
                        pos[1] / 2,
                        1 / 4 * IN,
                        mode=Mode.SUBTRACT,
                    )
                with Locations((pos[0] / 2, pos[1] + (width - pos[1]) / 2)):
                    RectangleRounded(
                        pos[0] / 2,
                        (width - pos[1] / 2) / 2,
                        1 / 4 * IN,
                        mode=Mode.SUBTRACT,
                    )
                with Locations(
                    (
                        pos[0] / 2 + corner_radius / 4,
                        pos[1] / 2 + corner_radius / 4,
                    )
                ):
                    Circle(radius=pos[0] / 4, mode=Mode.SUBTRACT)
            extrude(amount=thickness)
        p.part.label = "Router Jig"
        p.part.color = Color(0xB0EB00)
        return Compound(children=[p.part])
