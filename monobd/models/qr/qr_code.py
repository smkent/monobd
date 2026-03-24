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
    RectangleRounded,
    chamfer,
    extrude,
)

from ...common import Model

_FINDER_SIZE = 7  # finder patterns are always 7x7 modules
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
    # Rounding applied to module corners and finder pattern corners,
    # as a fraction of module size (0 = square, 0.5 = fully rounded ends)
    corner_radius_ratio: float = 0.25

    @staticmethod
    def _finder_cell_set(n: int) -> set[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()
        for fr, fc in [(0, 0), (0, n - _FINDER_SIZE), (n - _FINDER_SIZE, 0)]:
            for dr in range(_FINDER_SIZE):
                for dc in range(_FINDER_SIZE):
                    cells.add((fr + dr, fc + dc))
        return cells

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

        radius = module_size * self.corner_radius_ratio
        finder_cells = self._finder_cell_set(n)

        with BuildPart() as p_modules:
            with BuildSketch(Plane.XY.offset(self.base_thickness)):
                # Regular dark modules (skip finder pattern cells)
                for row in range(n):
                    for col in range(n):
                        if not matrix[row][col] or (row, col) in finder_cells:
                            continue
                        x = (col - n / 2 + 0.5) * module_size
                        y = (n / 2 - row - 0.5) * module_size
                        with Locations((x, y)):
                            RectangleRounded(
                                module_size, module_size, radius, mode=Mode.ADD
                            )
                # Finder patterns: outer ring + inner solid, both rounded
                for fr, fc in [
                    (0, 0),
                    (0, n - _FINDER_SIZE),
                    (n - _FINDER_SIZE, 0),
                ]:
                    cx = (fc + _FINDER_SIZE / 2 - n / 2) * module_size
                    cy = (n / 2 - fr - _FINDER_SIZE / 2) * module_size
                    with Locations((cx, cy)):
                        RectangleRounded(
                            _FINDER_SIZE * module_size,
                            _FINDER_SIZE * module_size,
                            radius,
                            mode=Mode.ADD,
                        )
                        RectangleRounded(
                            5 * module_size,
                            5 * module_size,
                            radius,
                            mode=Mode.SUBTRACT,
                        )
                        RectangleRounded(
                            3 * module_size,
                            3 * module_size,
                            radius,
                            mode=Mode.ADD,
                        )
            extrude(amount=self.module_height)
        p_modules.part.label = "modules"
        p_modules.part.color = Color(0x111111, alpha=0xFF)

        return Compound(
            label=self.model_name,
            children=[p_base.part, p_modules.part],
        )
