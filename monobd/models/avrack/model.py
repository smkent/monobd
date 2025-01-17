from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from build123d import IN, Color, Compound, Location

from ...common import Model
from . import constants
from .assets import asset
from .frame import RackFrame
from .tray import RackTray


@dataclass
class TrayConfig:
    label: str
    device_size: tuple[float, float, float]
    cutout_size: tuple[float, float]
    image_file: Path | None


@dataclass
class AVRack(Model, name="avrack"):
    simple: bool = False

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {"default": {}, "simple": {"simple": True}}

    @cached_property
    def trays_config(self) -> Iterator[TrayConfig]:
        yield from [
            TrayConfig(
                label="ethernet-switch",
                device_size=((6 + 5 / 16) * IN, (1 + 1 / 32) * IN, 4 * IN),
                cutout_size=((5 + 3 / 4) * IN, 13 / 16 * IN),
                image_file=asset("ethernet-port.svg"),
            ),
            TrayConfig(
                label="roku",
                device_size=(5 * IN, (1 + 1 / 32) * IN, 5 * IN),
                cutout_size=((3 + 1 / 2) * IN, (3 / 4) * IN),
                image_file=asset("roku-logo.svg"),
            ),
            TrayConfig(
                label="hdmi-duplicator",
                device_size=(
                    (6 + 1 / 2 - 1 / 32) * IN,
                    (3 / 4) * IN,
                    (2 + 1 / 2) * IN,
                ),
                cutout_size=(6 * IN, (19 / 32) * IN),
                image_file=asset("hdmi-port.svg"),
            ),
        ]

    @cached_property
    def assembly(self) -> Compound:
        frame = RackFrame()
        trays = [
            RackTray(
                label=c.label,
                device_size=c.device_size,
                cutout_size=c.cutout_size,
                image_file=c.image_file or "",
                hexagon_pattern=not self.simple,
            ).move(Location((0, 0, -constants.THICKNESS)))
            for c in self.trays_config
        ]
        for tray in trays:
            tray.color = Color(0xAAAAAA, alpha=0xFF)
        for i, loc in enumerate(constants.TRAY_LOCATIONS):
            trays[i] = trays[i].move(Location(loc))
        for i in range(2, len(trays)):
            trays[i] = trays[i].move(Location((0, constants.U * (i - 1), 0)))
        trays_assembly = Compound(  # type: ignore
            label="trays", children=trays
        )
        return Compound(  # type: ignore
            label=self.model_name, children=[frame, trays_assembly]
        )
