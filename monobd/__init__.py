"""A monorepository for my build123d models."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as import_version

from .common.registry import ModelRegistry

MODELS = ModelRegistry(
    {
        "avrack": "monobd.models.avrack.model.AVRack",
        "bikecard": "monobd.models.bikecard.model.BikeCardModel",
        "example": "monobd.models.example.ExampleModel",
        "poop_bag_dispenser_wall_mount": (
            "monobd.models.dog.PoopBagDispenserWallMount"
        ),
        "screw_handle": "monobd.models.hardware.ScrewHandle",
        "esp_3dp": "monobd.models.pcb.ESP3DP",
        "qr_code": "monobd.models.qr.QRCode",
    }
)

try:
    version = import_version(__name__)
except PackageNotFoundError:  # pragma: no cover
    version = "0.0.0"

__all__ = ["MODELS", "version"]
