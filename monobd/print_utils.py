from __future__ import annotations

from dataclasses import dataclass
from functools import partial, update_wrapper
from typing import TYPE_CHECKING

from build123d import MM, Compound, Location, Rotation, pack

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Concatenate, ParamSpec, TypeVar

    from build123d import Shape

    P = ParamSpec("P")
    R = TypeVar("R", bound=Shape)
    F = Callable[Concatenate[Any, P], R]


@dataclass
class PrintRotation:
    x: float = 0
    y: float = 0
    z: float = 0
    param: str = "print_orientation"

    def __call__(self, func: F) -> F:
        update_wrapper(self, func)
        return partial(self.wrapper, func)

    def wrapper(
        self,
        func: Callable[Concatenate[Any, P], R],
        inst: Any,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        result = func(inst, *args, **kwargs)
        if getattr(inst, self.param, False):
            return result.move(Rotation(self.x, self.y, self.z))
        return result


def arrange(
    *parts: Shape, padding: float = 5 * MM, pack_parts: bool = True
) -> Compound:
    pp = pack(parts, padding=padding, align_z=True) if pack_parts else parts
    model = Compound(children=list(pp))
    if pack_parts:
        bbox = model.bounding_box()
        model.move(Location((-bbox.max.X / 2, -bbox.max.Y / 2, 0)))
    return model
