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
    Circle,
    Color,
    Compound,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    chamfer,
    extrude,
    fillet,
)

from ...common import Model
from ...objects import SVGSketch
from .assets import asset

_FINDER_SIZE = 7  # finder patterns are always 7x7 modules
_DEFAULT_TEXT = "https://github.com/smkent/monobd"

_EC_LEVELS = {
    "L": qrcode_lib.constants.ERROR_CORRECT_L,
    "M": qrcode_lib.constants.ERROR_CORRECT_M,
    "Q": qrcode_lib.constants.ERROR_CORRECT_Q,
    "H": qrcode_lib.constants.ERROR_CORRECT_H,
}


@dataclass
class QRCode(Model, name="qr_code"):
    # Text/URL to encode
    text: str = _DEFAULT_TEXT
    # Overall side length of the QR code area (mm), excluding border
    size: float = 50.0
    # Thickness of the flat base plate (mm)
    base_thickness: float = 4.0
    # Height of raised QR modules above the base surface (mm)
    module_height: float = 0.6
    # Quiet-zone border around the QR code area (mm)
    border: float = 4.0
    edge_chamfer: float = 0.8
    corner_fillet: float = 5.0
    # Rounding applied to module corners and finder pattern corners,
    # as a fraction of module size (0 = square, 0.5 = fully rounded ends)
    corner_radius_ratio: float = 0.25
    # Error correction level: L (~7%), M (~15%), Q (~25%), H (~30%)
    error_correction: str = "H"
    # Logo area as a fraction of size (0 = no logo); keep <=0.3 for H level
    logo_size: float = 0.25

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
        qr = qrcode_lib.QRCode(
            border=0,
            error_correction=_EC_LEVELS[self.error_correction],
        )
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
            if self.corner_fillet > 0:
                fillet(p_base.edges().filter_by(Axis.Z), self.corner_fillet)
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

        # Build lookup of all dark cells for neighbor checks
        dark_set = {
            (row, col)
            for row in range(n)
            for col in range(n)
            if matrix[row][col]
        }

        # Compute center (x, y) in build123d coords for a matrix cell
        def cell_center(row: int, col: int) -> tuple[float, float]:
            return (
                (col - n / 2 + 0.5) * module_size,
                (n / 2 - row - 0.5) * module_size,
            )

        # Collect module centers and free-corner rounding positions.
        # For each corner: (row_delta_for_neighbor1, col_delta, row_delta2, col_delta2,
        #                    x_sign, y_sign)
        # x_sign/y_sign: -1 = left/bottom edge, +1 = right/top edge
        _corner_defs = [
            ((-1, 0), (0, -1), -1, +1),  # NW: no N and no W neighbor
            ((-1, 0), (0, +1), +1, +1),  # NE: no N and no E neighbor
            ((+1, 0), (0, +1), +1, -1),  # SE: no S and no E neighbor
            ((+1, 0), (0, -1), -1, -1),  # SW: no S and no W neighbor
        ]
        half = module_size / 2
        module_centers: list[tuple[float, float]] = []
        sub_positions: list[tuple[float, float]] = []
        arc_positions: list[tuple[float, float]] = []

        logo_half = self.logo_size * self.size / 2
        logo_cells = {
            (row, col)
            for row, col in dark_set
            if (
                abs(cell_center(row, col)[0]) < logo_half
                and abs(cell_center(row, col)[1]) < logo_half
            )
        }
        skip_cells = finder_cells | logo_cells

        for row, col in dark_set - skip_cells:
            cx, cy = cell_center(row, col)
            module_centers.append((cx, cy))
            if radius > 0:
                for (dn1, dc1), (dn2, dc2), sx, sy in _corner_defs:
                    if (row + dn1, col + dc1) not in dark_set and (
                        row + dn2,
                        col + dc2,
                    ) not in dark_set:
                        sub_positions.append(
                            (
                                cx + sx * (half - radius / 2),
                                cy + sy * (half - radius / 2),
                            )
                        )
                        arc_positions.append(
                            (
                                cx + sx * (half - radius),
                                cy + sy * (half - radius),
                            )
                        )

        with BuildPart() as p_modules:
            with BuildSketch(Plane.XY.offset(self.base_thickness)):
                # All regular dark modules as plain squares
                with Locations(module_centers):
                    Rectangle(module_size, module_size, mode=Mode.ADD)
                # Knock out free corners, then restore quarter-circle arcs
                if sub_positions:
                    with Locations(sub_positions):
                        Rectangle(radius, radius, mode=Mode.SUBTRACT)
                    with Locations(arc_positions):
                        Circle(radius, mode=Mode.ADD)
                # Finder patterns: outer ring + inner solid, uniformly rounded
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
                # SVG logo in the center
                if logo_half > 0:
                    SVGSketch(
                        asset("ethernet-port.svg"),
                        size=logo_half * 2 * 0.85,
                        mode=Mode.ADD,
                    )
            extrude(amount=self.module_height)
        p_modules.part.label = "modules"
        p_modules.part.color = Color(0x111111, alpha=0xFF)

        return Compound(
            label=self.model_name,
            children=[p_base.part, p_modules.part],
        )
