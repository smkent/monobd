import pytest
from pytest import approx

from monobd.models.qr import QRCode


@pytest.mark.parametrize(
    ["variant_name", "expected_plate_size"],
    [
        pytest.param("default", 58.0, id="default"),
        pytest.param("small", 43.0, id="small"),
        pytest.param("large", 88.0, id="large"),
    ],
)
def test_qr_code_plate_size(
    variant_name: str, expected_plate_size: float
) -> None:
    model = QRCode.variant(variant_name)
    assert isinstance(model, QRCode)
    assert model.plate_size == approx(expected_plate_size)


def test_qr_code_assembly() -> None:
    model = QRCode.variant("default")
    assert len(model.assembly.leaves) == 2
    bb = model.assembly.bounding_box()
    assert bb.size.X == approx(58.0)
    assert bb.size.Y == approx(58.0)
    # total height = base_thickness + module_height
    assert bb.size.Z == approx(4.6)
    assert sorted(model.export_parts.keys()) == [
        "qr_code-default",
        "qr_code-default.base",
        "qr_code-default.modules",
    ]
