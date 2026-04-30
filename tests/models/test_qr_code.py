import pytest

from monobd.models.qr.qr_code import QRCode


@pytest.mark.parametrize(
    ("variant_name", "expected_plate_size"),
    [
        pytest.param(None, 58.0, id="default"),
        pytest.param("small", 43.0, id="small"),
        pytest.param("large", 88.0, id="large"),
    ],
)
def test_qr_code_plate_size(
    variant_name: str | None, expected_plate_size: float
) -> None:
    model = QRCode.with_preset(variant_name)
    assert isinstance(model, QRCode)
    assert model.plate_size == pytest.approx(expected_plate_size)


def test_qr_code_assembly() -> None:
    model = QRCode()
    assembly = model.build()
    assert len(assembly.leaves) == 2
    bb = assembly.bounding_box()
    assert pytest.approx(58.0) == bb.size.X
    assert pytest.approx(58.0) == bb.size.Y
    # total height = base_thickness + module_height
    assert pytest.approx(4.6) == bb.size.Z
