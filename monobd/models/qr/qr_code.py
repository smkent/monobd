from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any

import qrcode as qrcode_lib
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Color,
    Compound,
    Locations,
    Mode,
    Plane,
    Rectangle,
    chamfer,
    extrude,
)

from ...common import Model

_DEFAULT_TEXT = "https://github.com/smkent/monobd"


@dataclass
class QRCode(Model, name="qr_code"):
    # Text/URL to encode
    text: str = _DEFAULT_TEXT
    # Overall side length of the QR code area (mm), excluding border
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

    def _qr_matrix(self) -> list[list[bool]]:
        qr = qrcode_lib.QRCode(border=0)
        qr.add_data(self.text)
        qr.make(fit=True)
        return qr.get_matrix()

    @cached_property
    def assembly(self) -> Compound:
        matrix = self._qr_matrix()
        n = len(matrix)
        module_size = self.size / n

        with BuildPart() as p_base:
            Box(
                self.plate_size,
                self.plate_size,
                self.base_thickness,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            chamfer(
                p_base.edges().filter_by(Plane.XY).group_by(Axis.Z)[-1],
                self.edge_chamfer,
            )
            chamfer(
                p_base.edges().filter_by(Plane.XY).group_by(Axis.Z)[0],
                self.edge_chamfer,
            )
        p_base.part.label = "base"
        p_base.part.color = Color(0xFFFFFF, alpha=0xFF)

        with BuildPart() as p_modules:
            with BuildSketch(Plane.XY.offset(self.base_thickness)):
                for row in range(n):
                    for col in range(n):
                        if not matrix[row][col]:
                            continue
                        # matrix row 0 is the top of the QR code; col 0 is left
                        x = (col - n / 2 + 0.5) * module_size
                        y = (n / 2 - row - 0.5) * module_size
                        with Locations((x, y)):
                            Rectangle(module_size, module_size, mode=Mode.ADD)
            extrude(amount=self.module_height)
        p_modules.part.label = "modules"
        p_modules.part.color = Color(0x111111, alpha=0xFF)

        return Compound(
            label=self.model_name,
            children=[p_base.part, p_modules.part],
        )
