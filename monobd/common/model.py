from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar

from build123d import Compound, export_step


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
    def variant(cls, variant_name: str, default: bool = True) -> Model:
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

    def _part_fq_name(self, part: Compound) -> str:
        path_parts = [c.label for c in part.path]
        if self.variant_name:
            path_parts[0] += f"-{self.variant_name}"
        return ".".join(path_parts)

    def export_to_step(self, dest: Path | None = None) -> None:
        def _export_step(assembly: Compound, path: Path) -> None:
            print(f"Exporting {path}")
            export_step(assembly, path)

        dest = dest or Path(".")
        dest.mkdir(exist_ok=True)
        assembly_part_name = self._part_fq_name(self.assembly)
        if len(self.assembly.leaves) == 1:
            _export_step(self.assembly, dest / f"{assembly_part_name}.step")
            return
        export_files = {f"{assembly_part_name}": self.assembly}
        for part in self.assembly.leaves:
            part_name = self._part_fq_name(part)
            if part_name in export_files:
                raise Exception(f"Duplicate part name {part_name}")
            export_files[part_name] = part
        for part_name, part in export_files.items():
            _export_step(part, dest / f"{part_name}.step")
