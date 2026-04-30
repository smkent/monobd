import pytest

from monobd.models.example import ExampleModel


@pytest.mark.parametrize(
    ("preset", "expected_size"),
    [
        pytest.param(None, [20, 20, 30], id="default"),
        pytest.param("tall", [20, 20, 60], id="tall"),
    ],
)
def test_example_model(
    preset: str | None, expected_size: tuple[float, float, float]
) -> None:
    model = ExampleModel.with_preset(preset=preset)
    assembly = model.build()
    assert len(assembly.leaves) == 2
    bounding_box = assembly.bounding_box()
    assert list(bounding_box.size) == pytest.approx(expected_size)
