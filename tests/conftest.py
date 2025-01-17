from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    with TemporaryDirectory(prefix="monobd.unittest.") as td:
        yield Path(td)
