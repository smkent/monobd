from __future__ import annotations

from build123d import MM, Compound, Location, Shape, pack


def arrange(
    *parts: Shape, padding: float = 5 * MM, pack_parts: bool = True
) -> Compound:
    pp = pack(parts, padding=padding, align_z=True) if pack_parts else parts
    model = Compound(children=list(pp))
    if pack_parts:
        bbox = model.bounding_box()
        model.move(Location((-bbox.max.X / 2, -bbox.max.Y / 2, 0)))
    return model
