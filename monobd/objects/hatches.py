from build123d import (
    MM,
    Align,
    BaseSketchObject,
    BuildSketch,
    Location,
    Locations,
    Mode,
    Rectangle,
)


class HatchPattern(BaseSketchObject):
    def __init__(
        self,
        width: float,
        height: float,
        hatch_width: float = 4 * MM,
        hatch_rotation: float = 45,
        rotation: float = 0,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ) -> None:
        with BuildSketch() as sk:
            with Locations(Location((0, 0, 0), (0, 0, hatch_rotation))):
                max_dim = max(width, height)
                count = int(max_dim / hatch_width)
                with Locations(
                    [(hatch_width * i, 0, 0) for i in range(-count, count)]
                ):
                    Rectangle(hatch_width / 2, max_dim * 2)
            Rectangle(width, height, mode=Mode.INTERSECT)
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )
