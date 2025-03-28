from build123d import (
    Align,
    Axis,
    BasePartObject,
    BuildPart,
    BuildSketch,
    Circle,
    CounterBoreHole,
    Mode,
    Rectangle,
    RotationLike,
    extrude,
    validate_inputs,
)


class PrintableCounterBoreHole(BasePartObject):
    def __init__(
        self,
        radius: float,
        counter_bore_radius: float,
        counter_bore_depth: float,
        depth: float | None = None,
        rotation: RotationLike = (0, 0, 0),
        align: tuple[Align, Align, Align] = (
            Align.CENTER,
            Align.CENTER,
            Align.CENTER,
        ),
        mode: Mode = Mode.SUBTRACT,
    ):
        context: BuildPart | None = BuildPart._get_context(self)
        validate_inputs(context, self)
        if depth is None and context is not None:
            depth = context.max_dimension
        else:
            raise ValueError("No depth provided")
        with BuildPart() as p:
            CounterBoreHole(
                radius=radius,
                counter_bore_radius=counter_bore_radius,
                counter_bore_depth=counter_bore_depth,
                depth=depth,
                mode=Mode.ADD,
            )
            with BuildSketch(p.faces().sort_by(Axis.Z)[2]) as sk:
                Circle(radius=counter_bore_radius)
                Rectangle(
                    counter_bore_radius,
                    counter_bore_radius * 2,
                    mode=Mode.SUBTRACT,
                )
            extrude(sk.sketch, amount=-0.4, mode=Mode.SUBTRACT)
        super().__init__(
            part=p.part, rotation=rotation, align=align, mode=mode
        )
