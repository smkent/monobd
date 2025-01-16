from build123d import (
    Align,
    BasePartObject,
    Box,
    BuildPart,
    Mode,
    RotationLike,
    fillet,
)


class ExamplePart(BasePartObject):
    def __init__(
        self,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as p:
            Box(10, 20, 30)
            fillet(p.edges(), radius=2)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )
