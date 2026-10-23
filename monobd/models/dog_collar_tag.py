from __future__ import annotations

from bdbox import Model
from build123d import (
    MM,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    FontStyle,
    Locations,
    Mode,
    Plane,
    Pos,
    Text,
    TextAlign,
    extrude,
)


class DogCollarTag(Model):
    name: str = "Spot"
    phone: str = "555.555.5555"
    width: float = 25
    length: float = 25
    thickness: float = 3
    text_thickness: float = 0.4

    def build(self) -> Model.Geometry:
        with BuildPart() as p:
            with BuildSketch():
                Circle(radius=self.width / 2)
                with Locations(Pos((0, self.width / 2 - (3.75 * MM)))):
                    Circle(radius=(3.5 * MM) / 2, mode=Mode.SUBTRACT)
            extrude(amount=self.thickness)
            with BuildSketch(Plane.XY.offset(self.thickness)):
                with Locations(Pos(0, 0, 0)):
                    Text(
                        self.name,
                        font_size=self.width / 4,
                        font_style=FontStyle.BOLD,
                        text_align=(TextAlign.CENTER, TextAlign.BOTTOM),
                    )
                phone_str = "".join(filter(str.isdigit, self.phone))
                area, prefix, num = (
                    phone_str[:3],
                    phone_str[3:6],
                    phone_str[6:],
                )
                phone_sz = self.width / 5
                with Locations(Pos(0, -(self.width / 4 * 0), 0)):
                    Text(
                        f"{area}-{prefix}-",
                        font_size=phone_sz,
                        font_style=FontStyle.BOLD,
                        text_align=(TextAlign.CENTER, TextAlign.TOP),
                    )
                with Locations(Pos(0, -phone_sz, 0)):
                    Text(
                        f"{num}",
                        font_size=phone_sz,
                        font_style=FontStyle.BOLD,
                        text_align=(TextAlign.CENTER, TextAlign.TOP),
                    )

            extrude(amount=self.text_thickness, mode=Mode.ADD)

        if not p.part:
            raise RuntimeError("Empty part")
        p.part.label = "tag"
        p.part.color = Color(0x6633CC)
        return p.part
