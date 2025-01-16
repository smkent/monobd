from build123d import Color, Compound, export_step
from ocp_vscode import show  # type: ignore

from .parts.example import ExamplePart


def main() -> None:
    bp = ExamplePart()
    bp.label = "orange_box"
    bp.color = Color(0xFF8822, alpha=0x99)
    assembly = Compound(label="assembly", children=[bp])  # type: ignore
    show(assembly, axes=True, axes0=True, transparent=False)
    export_step(assembly, "example.step")
