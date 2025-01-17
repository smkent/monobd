from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import Any

from build123d import IN, Compound, Location

from ...common import Model
from . import constants
from .assets import asset
from .frame import RackFrame
from .tray import RackTray


@dataclass
class AVRack(Model, name="avrack"):
    simple: bool = False

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {"default": {}, "simple": {"simple": True}}

    @cached_property
    def assembly(self) -> Compound:
        frame = RackFrame()
        rt = RackTray(
            device_size=((6 + 5 / 16) * IN, (1 + 1 / 32) * IN, 4 * IN),
            cutout_size=((5 + 3 / 4) * IN, 13 / 16 * IN),
            image_file=asset("ethernet-port.svg"),
            label="ethernet-switch",
            hexagon_pattern=not self.simple,
        )
        rt = rt.move(Location(constants.TRAY_LOCATIONS[0]))
        rt = rt.move(Location((0, 0, -constants.THICKNESS)))
        rt2 = RackTray(
            device_size=(5 * IN, (1 + 1 / 32) * IN, 5 * IN),
            cutout_size=((3 + 1 / 2) * IN, (3 / 4) * IN),
            image_file=asset("roku-logo.svg"),
            label="roku",
            hexagon_pattern=not self.simple,
        )
        rt2 = rt2.move(Location(constants.TRAY_LOCATIONS[1]))
        rt2 = rt2.move(Location((0, 0, -constants.THICKNESS)))
        rt3 = RackTray(
            device_size=(
                (6 + 1 / 2 - 1 / 32) * IN,
                (3 / 4) * IN,
                (2 + 1 / 2) * IN,
            ),
            cutout_size=(6 * IN, (19 / 32) * IN),
            image_file=asset("hdmi-port.svg"),
            label="hdmi-duplicator",
            hexagon_pattern=not self.simple,
        )
        rt3 = rt3.move(Location((0, 1 * constants.U, -constants.THICKNESS)))
        trays = Compound(  # type: ignore
            label="trays", children=[rt, rt2, rt3]
        )
        return Compound(  # type: ignore
            label=self.model_name, children=[frame, trays]
        )
