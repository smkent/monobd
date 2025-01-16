from functools import cached_property

from build123d import Compound, export_step


class BaseModel:
    @cached_property
    def model(self) -> Compound:
        raise NotImplementedError

    def export_to_step(self) -> None:
        if len(self.model.leaves) == 1:
            export_step(self.model, f"{self.model.label}.step")
            return
        export_files = {f"{self.model.label}.all_parts": self.model}
        for part in self.model.leaves:
            part_name = ".".join([c.label for c in part.path])
            if part_name in export_files:
                raise Exception(f"Duplicate part name {part_name}")
            export_files[part_name] = part
        for part_name, part in export_files.items():
            export_step(part, f"{part_name}.step")
