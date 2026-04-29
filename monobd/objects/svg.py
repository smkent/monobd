from pathlib import Path

from build123d import (
    Align,
    BaseSketchObject,
    BuildSketch,
    Mode,
    Plane,
    add,
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
        *,
        flip_x: bool = True,
    ) -> None:
        with BuildSketch() as sk:
            ep = import_svg(str(file_name))
            if flip_x:
                ep = mirror(ep, about=Plane.YZ, mode=Mode.PRIVATE)
            add(ep)
            bbox = sk.sketch.bounding_box()
            max_dim = max(bbox.size.Y, bbox.size.X)
            ep = scale(ep, by=(size / max_dim))
        super().__init__(
            obj=sk.sketch, rotation=rotation, align=align, mode=mode
        )
