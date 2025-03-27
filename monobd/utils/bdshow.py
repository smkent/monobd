from __future__ import annotations

from argparse import ArgumentParser, Namespace
from functools import cached_property

from ocp_vscode import show  # type: ignore

from ..common import Model


class ModelDisplay:
    @cached_property
    def args(self) -> Namespace:
        ap = ArgumentParser(description="Show monobd model in OCP viewer")
        ap.add_argument("model_name", metavar="model", help="Model to show")
        ap.add_argument(
            "variant_name", nargs="?", default="", help="Model variant name"
        )
        return ap.parse_args()

    def __call__(self) -> None:
        assert self.args
        print("Rendering model")
        model = Model._models[self.args.model_name].variant(
            self.args.variant_name
        )
        print(model.assembly.show_topology())
        print("Displaying model")
        show(model.assembly, axes=True, axes0=True, transparent=False)


def main() -> None:
    ModelDisplay()()


if __name__ == "__main__":
    main()
