from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    Color,
    Compound,
    Plane,
    chamfer,
)

from ...common import Model


@dataclass
class QRCode(Model, name="qr_code"):
    # Overall side length of the QR code square (mm)
    size: float = 50.0
    # Thickness of the flat base plate (mm)
    base_thickness: float = 2.0
    # Height of raised QR modules above the base surface (mm)
    module_height: float = 1.0
    # Quiet-zone border around the QR code area (mm)
    border: float = 4.0
    edge_chamfer: float = 0.8

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "default": {},
            "small": {"size": 35.0},
            "large": {"size": 80.0},
        }

    @property
    def plate_size(self) -> float:
        """Total plate side length including border on each side."""
        return self.size + self.border * 2

    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            Box(
                self.plate_size,
                self.plate_size,
                self.base_thickness,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            chamfer(
                p.edges().filter_by(Plane.XY).group_by(Axis.Z)[-1],
                self.edge_chamfer,
            )
            chamfer(
                p.edges().filter_by(Plane.XY).group_by(Axis.Z)[0],
                self.edge_chamfer,
            )

        p.part.label = "base"
        p.part.color = Color(0xDDDDDD, alpha=0xFF)
        return Compound(label=self.model_name, children=[p.part])
