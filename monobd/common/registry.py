from __future__ import annotations

from importlib import import_module

from .model import Model


class ModelRegistry(dict):
    def get_model(self, model_name: str) -> type[Model]:
        if not (import_path := self.get(model_name)):
            raise KeyError(f"Model not found: {model_name}")
        module_path, class_name = import_path.rsplit(".", 1)
        module = import_module(module_path)
        model_cls = getattr(module, class_name)
        assert isinstance(model_cls, type)
        assert issubclass(model_cls, Model)
        return model_cls
