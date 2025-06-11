from .__version__ import __version__ as version
from .common.registry import ModelRegistry

MODELS = ModelRegistry(
    {
        "avrack": "monobd.models.avrack.model.AVRack",
        "example": "monobd.models.example.ExampleModel",
        "poop_bag_dispenser_wall_mount": (
            "monobd.models.dog.PoopBagDispenserWallMount"
        ),
        "screw_handle": "monobd.models.hardware.ScrewHandle",
        "esp_3dp": "monobd.models.pcb.ESP3DP",
    }
)

__all__ = ["version", "MODELS"]
