from pathlib import Path


def asset(name: str) -> Path:
    return Path(__file__).parent / name
