from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path

from ..common import Model


class ModelRenderer:
    @cached_property
    def args(self) -> Namespace:
        ap = ArgumentParser("Render monobd models")
        ap.add_argument(
            "model_name",
            nargs="?",
            metavar="model",
            help="Model(s) to render (default: do nothing)",
        )
        ap.add_argument(
            "variant_name",
            nargs="?",
            default="",
            help="Model variant name (default: all variants)",
        )
        ap.add_argument(
            "-a",
            "--all",
            dest="render_all",
            action="store_true",
            help="Render all models",
        )
        ap.add_argument(
            "-d",
            "--destination",
            dest="dest",
            type=Path,
            metavar="dir",
            default=Path(".") / "renders",
            help="Destination directory (default: %(default)s)",
        )
        return ap.parse_args()

    def render_models(self) -> Iterator[type[Model]]:
        if self.args.model_name:
            yield Model._models[self.args.model_name]
            return
        if self.args.render_all:
            yield from Model._models.values()

    def render_variants(self, model_class: type[Model]) -> Iterator[Model]:
        if self.args.variant_name:
            yield model_class.variant(self.args.variant_name, default=False)
            return
        yield from model_class.all_variants()

    def __call__(self) -> None:
        try:
            for model_class in self.render_models():
                for model in self.render_variants(model_class):
                    print(
                        f"Rendering {model_class.__name__} model"
                        + (
                            f" variant {model.variant_name}"
                            if model.variant_name
                            else ""
                        )
                    )
                    print(model.assembly.show_topology())
                    print("Exporting model")
                    model.export_to_step(self.args.dest)
                    print("")
        except KeyboardInterrupt:
            print("")
            raise


def main() -> None:
    ModelRenderer()()


if __name__ == "__main__":
    main()
