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
        raise NotImplementedError

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

    def export_to_step(self, dest: Path | None = None) -> None:
        dest = dest or Path(".")
        dest.mkdir(exist_ok=True)
        prefix = f"{self.variant_name}-"
        if len(self.assembly.leaves) == 1:
            export_step(
                self.assembly, dest / f"{prefix}{self.assembly.label}.step"
            )
            return
        export_files = {f"{self.assembly.label}.all_parts": self.assembly}
        for part in self.assembly.leaves:
            part_name = ".".join([c.label for c in part.path])
            if part_name in export_files:
                raise Exception(f"Duplicate part name {part_name}")
            export_files[part_name] = part
        for part_name, part in export_files.items():
            export_step(part, dest / f"{prefix}{part_name}.step")
