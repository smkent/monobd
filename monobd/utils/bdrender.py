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
            "model_name", metavar="model", help="Model(s) to render"
        )
        ap.add_argument(
            "variant_name",
            nargs="?",
            default="",
            help="Model variant name (default: all variants)",
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

    def render_variants(self) -> Iterator[Model]:
        model_class = Model._models[self.args.model_name]
        if self.args.variant_name:
            yield model_class.variant(self.args.variant_name, default=False)
            return
        yield from model_class.all_variants()

    def __call__(self) -> None:
        try:
            for model in self.render_variants():
                print(model.assembly.show_topology())
                model.export_to_step(self.args.dest)
        except KeyboardInterrupt:
            print("")
            raise


def main() -> None:
    ModelRenderer()()


if __name__ == "__main__":
    main()
