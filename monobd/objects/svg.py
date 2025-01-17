from pathlib import Path

from build123d import (
    Align,
    BaseSketchObject,
    BuildSketch,
    Mode,
    Plane,
    import_svg,
    mirror,
    scale,
)


class SVGSketch(BaseSketchObject):
    def __init__(
        self,
        file_name: str | Path,
        size: float,
        rotation: float = 180,
        align: tuple[Align, Align] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        with BuildSketch() as sk:
            ep = import_svg(str(file_name))
            ep = mirror(ep, about=Plane.YZ)
            max_dim = max(ep.bounding_box().size.Y, ep.bounding_box().size.X)
            ep = scale(ep, by=(size / max_dim))
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )
