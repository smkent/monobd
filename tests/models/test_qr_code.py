import pytest
from pytest import approx

from monobd import MODELS

QRCode = MODELS.get_model("qr_code")


@pytest.mark.parametrize(
    ["variant_name", "expected_plate_size"],
    [
        pytest.param("default", 58.0, id="default"),
        pytest.param("small", 43.0, id="small"),
        pytest.param("large", 88.0, id="large"),
    ],
)
def test_qr_code_plate_size(variant_name: str, expected_plate_size: float) -> None:
    model = QRCode.variant(variant_name)
    assert model.plate_size == approx(expected_plate_size)


def test_qr_code_assembly() -> None:
    model = QRCode.variant("default")
    assert len(model.assembly.leaves) == 1
    bb = model.assembly.bounding_box()
    assert bb.size.X == approx(58.0)
    assert bb.size.Y == approx(58.0)
    # total height = base_thickness + module_height
    assert bb.size.Z == approx(3.0)
