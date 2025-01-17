from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar

from build123d import Compound, export_step, export_stl


@dataclass
class Model:
    _models: ClassVar[dict[str, type[Model]]] = {}
    model_name: ClassVar[str] = ""
    variant_name: str = ""

    def __init_subclass__(cls, name: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.model_name = name
        cls._models[name] = cls

    @cached_property
    def assembly(self) -> Compound:
        raise NotImplementedError

    @classmethod
    def variants(cls) -> dict[str, dict[str, Any]]:
        return {}

    @classmethod
    def variant(cls, variant_name: str | None, default: bool = True) -> Model:
        variant_name = variant_name or ""
        variants = cls.variants()
        if default and variant_name not in variants:
            return cls()
        return cls(variant_name=variant_name, **variants[variant_name])

    @classmethod
    def all_variants(cls) -> Iterator[Model]:
        if not (variants := cls.variants()):
            yield cls()
            return
        for variant_name, params in variants.items():
            yield cls(variant_name=variant_name, **params)

    @cached_property
    def export_parts(self) -> dict[str, Compound]:
        def _part_fq_name(part: Compound) -> str:
            path_parts = [c.label for c in part.path]
            if self.variant_name:
                path_parts[0] += f"-{self.variant_name}"
            return ".".join(path_parts)

        assembly_part_name = _part_fq_name(self.assembly)
        export_parts = {assembly_part_name: self.assembly}
        if len(self.assembly.leaves) == 1:
            export_parts[assembly_part_name] = self.assembly.leaves[0]
        else:
            for part in self.assembly.leaves:
                part_name = _part_fq_name(part)
                if part_name in export_parts:
                    raise Exception(f"Duplicate part name {part_name}")
                export_parts[part_name] = part
        return export_parts

    def export(
        self, dest: Path | None = None, step: bool = True, stl: bool = False
    ) -> None:
        def _export_step(assembly: Compound, path: Path) -> None:
            print(f"Exporting {path}")
            export_step(assembly, path)

        def _export_stl(assembly: Compound, path: Path) -> None:
            print(f"Exporting {path}")
            export_stl(assembly, path)

        dest = dest or Path(".")
        dest.mkdir(exist_ok=True)
        for part_name, part in self.export_parts.items():
            if step:
                _export_step(part, dest / f"{part_name}.step")
            if stl and part.is_leaf:
                _export_stl(part, dest / f"{part_name}.stl")
