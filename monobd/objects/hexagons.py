import math
from functools import cached_property

from build123d import (
    Align,
    BaseSketchObject,
    BoundBox,
    BuildSketch,
    HexLocations,
    Location,
    Locations,
    Mode,
    Rectangle,
    RegularPolygon,
)


class HexagonPattern(BaseSketchObject):
    def __init__(
        self,
        width: float,
        height: float,
        hex_size: float = 8,
        hex_spacing: float = 1.4,
        whole_only: bool = False,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        self._width = width
        self._height = height
        self.hex_size = hex_size
        self.hex_spacing = hex_spacing
        self.whole_only = whole_only
        with BuildSketch() as sk:
            with Locations(self.locations):
                RegularPolygon(radius=hex_size, side_count=6)
            Rectangle(width, height, mode=Mode.INTERSECT)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )

    @cached_property
    def locations(self) -> list[Location]:
        all_hex_locations = HexLocations(
            radius=self.hex_size + self.hex_spacing,
            x_count=self.x_count,
            y_count=self.y_count,
            major_radius=True,
        )
        if not self.whole_only:
            return all_hex_locations.locations
        rect = Rectangle(self._width, self._height, mode=Mode.PRIVATE)
        whole_hex_locations = []
        for loc in all_hex_locations:
            with Locations(loc):
                rp = RegularPolygon(
                    radius=self.hex_size, side_count=6, mode=Mode.PRIVATE
                )
                if (
                    BoundBox.find_outside_box_2d(
                        rp.bounding_box(), rect.bounding_box()
                    )
                    is not None
                ):
                    whole_hex_locations.append(loc)
        return whole_hex_locations

    @cached_property
    def x_count(self) -> int:
        return math.ceil(
            self._width / (self.hex_size * 1.5 + self.hex_spacing)
        )

    @cached_property
    def y_count(self) -> int:
        return math.ceil(
            self._height / (self.hex_size * 1.5 + self.hex_spacing)
        )
