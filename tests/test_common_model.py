from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Any

import pytest
from build123d import Box, BuildPart, Compound
from pytest import approx

from monobd.common import Model


@dataclass
class SimpleTestModel(Model, name="testmodel"):
    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            Box(10, 20, 30)
        p.part.label = "box"
        return Compound(label=self.model_name, children=[p.part])


@dataclass
class VariantTestModel(Model, name="variantmodel"):
    size: int = 10

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {
            "": {},
            "large": {"size": 20},
            "small": {"size": 5},
        }

    @cached_property
    def assembly(self) -> Compound:
        with BuildPart() as p:
            Box(self.size, self.size * 2, self.size * 3)
        p.part.label = "box"
        return Compound(label=self.model_name, children=[p.part])


@pytest.fixture
def model() -> Iterator[SimpleTestModel]:
    instance = SimpleTestModel()
    assert instance.__class__.variants() == {}
    yield instance


def test_model(model: SimpleTestModel) -> None:
    assert len(model.assembly.leaves) == 1
    bounding_box = model.assembly.bounding_box()
    assert [i for i in bounding_box.size] == approx([10, 20, 30])
    assert sorted(model.export_parts.keys()) == ["testmodel"]


@pytest.mark.parametrize(
    ["model_class", "expected_variant_names"],
    (
        pytest.param(SimpleTestModel, {""}),
        pytest.param(VariantTestModel, {"", "small", "large"}),
    ),
)
def test_model_all_variants(
    model_class: type[Model], expected_variant_names: set[str]
) -> None:
    assert {
        v.variant_name for v in model_class.all_variants()
    } == expected_variant_names


@pytest.mark.parametrize(
    ["step", "stl", "expected_files"],
    (
        pytest.param(True, False, {"testmodel.step"}, id="step"),
        pytest.param(False, True, {"testmodel.stl"}, id="stl"),
        pytest.param(
            True, True, {"testmodel.step", "testmodel.stl"}, id="step_and_stl"
        ),
    ),
)
def test_simple_model_export(
    model: SimpleTestModel,
    temp_dir: Path,
    step: bool,
    stl: bool,
    expected_files: set[str],
) -> None:
    model.export(temp_dir, step=step, stl=stl)
    assert {
        fn.name for fn in temp_dir.iterdir() if fn.is_file()
    } == expected_files


@pytest.mark.parametrize(
    ["variant_name", "step", "stl", "expected_files"],
    chain(
        *(
            (
                pytest.param(
                    vn,
                    True,
                    False,
                    {f"variantmodel{f'-{vn}' if vn else ''}.step"},
                    id=f"{vn or 'empty_name'}-step",
                ),
                pytest.param(
                    vn,
                    False,
                    True,
                    {f"variantmodel{f'-{vn}' if vn else ''}.stl"},
                    id=f"{vn or 'empty_name'}-stl",
                ),
                pytest.param(
                    vn,
                    True,
                    True,
                    {
                        f"variantmodel{f'-{vn}' if vn else ''}.step",
                        f"variantmodel{f'-{vn}' if vn else ''}.stl",
                    },
                    id=f"{vn or 'empty_name'}-step_and_stl",
                ),
            )
            for vn in VariantTestModel.variants().keys()
        )
    ),
)
def test_variant_model_export(
    variant_name: str,
    temp_dir: Path,
    step: bool,
    stl: bool,
    expected_files: set[str],
) -> None:
    model = VariantTestModel.variant(variant_name)
    model.export(temp_dir, step=step, stl=stl)
    assert {
        fn.name for fn in temp_dir.iterdir() if fn.is_file()
    } == expected_files
