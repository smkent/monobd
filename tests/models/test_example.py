import pytest
from pytest import approx

from monobd.models import ExampleModel


@pytest.mark.parametrize(
    ["variant_name", "expected_size"],
    [
        pytest.param("default", [20, 20, 30], id="default"),
        pytest.param("tall", [20, 20, 60], id="tall"),
    ],
)
def test_example_model(
    variant_name: str, expected_size: tuple[float, float, float]
) -> None:
    model = ExampleModel.variant(variant_name)
    assert len(model.assembly.leaves) == 2
    bounding_box = model.assembly.bounding_box()
    assert [i for i in bounding_box.size] == approx(expected_size)
    assert sorted(model.export_parts.keys()) == [
        f"example-{variant_name}",
        f"example-{variant_name}.green_box",
        f"example-{variant_name}.orange_box",
    ]
