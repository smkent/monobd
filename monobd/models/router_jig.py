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
    length: float = 6 * IN
    width: float = 6 * IN
    thickness: float = 4 * MM
    corner_radius: float = 1 * IN

    def build(self) -> Compound:
        with BuildPart() as p:
            with BuildSketch() as sk:
                Rectangle(
                    self.length, self.width, align=(Align.MIN, Align.MIN)
                )
                fillet(
                    sk.vertices().sort_by_distance((0, 0))[0],
                    radius=self.corner_radius,
                )
                pos = (2 * IN,) * 2
                with Locations(pos):
                    Rectangle(
                        self.length,
                        self.width,
                        align=(Align.MIN, Align.MIN),
                        mode=Mode.SUBTRACT,
                    )
                    fillet(
                        sk.vertices().sort_by_distance(pos)[0],
                        radius=self.corner_radius / 2,
                    )
                fillet(
                    sk.vertices().sort_by_distance((self.length, 0))[:2],
                    radius=(1 / 4) * IN,
                )
                fillet(
                    sk.vertices().sort_by_distance((0, self.width))[:2],
                    radius=(1 / 4) * IN,
                )
                with Locations(
                    (pos[0] + (self.length - pos[0]) / 2, pos[1] / 2)
                ):
                    RectangleRounded(
                        (self.length - pos[0] / 2) / 2,
                        pos[1] / 2,
                        1 / 4 * IN,
                        mode=Mode.SUBTRACT,
                    )
                with Locations(
                    (pos[0] / 2, pos[1] + (self.width - pos[1]) / 2)
                ):
                    RectangleRounded(
                        pos[0] / 2,
                        (self.width - pos[1] / 2) / 2,
                        1 / 4 * IN,
                        mode=Mode.SUBTRACT,
                    )
                with Locations(
                    (
                        pos[0] / 2 + self.corner_radius / 4,
                        pos[1] / 2 + self.corner_radius / 4,
                    )
                ):
                    Circle(radius=pos[0] / 4, mode=Mode.SUBTRACT)
            extrude(amount=self.thickness)
        p.part.label = "orange_box"
        p.part.color = Color(0xFF8822, alpha=0x99)
        return Compound(children=[p.part])
