from __future__ import annotations

import subprocess  # nosec B404
import sys
import time
import traceback
import webbrowser
from argparse import ArgumentParser, Namespace
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cached_property
from importlib import import_module, reload
from threading import Condition, Event, Thread
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import urlopen

from ocp_vscode import show  # type: ignore
from ocp_vscode.comms import CMD_PORT as OCP_VIEWER_PORT  # type: ignore
from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

from ..common import BaseModel


class Watcher:
    class EventHandler(PatternMatchingEventHandler):
        def __init__(
            self, callback: Callable[[], None], *args: Any, **kwargs: Any
        ):
            super().__init__(*args, **kwargs)
            self.callback = callback

        def on_created(
            self, event: DirCreatedEvent | FileCreatedEvent
        ) -> None:
            self.callback()

        def on_modified(
            self, event: DirModifiedEvent | FileModifiedEvent
        ) -> None:
            self.callback()

    def __call__(self) -> None:
        with self.ocp_viewer(), self.event_watcher():
            try:
                while True:
                    time.sleep(1000)
            except KeyboardInterrupt:
                print("")

    @cached_property
    def args(self) -> Namespace:
        ap = ArgumentParser("Model automatic renderer for development")
        ap.add_argument(
            "--no-viewer",
            "-N",
            dest="viewer",
            action="store_false",
            help="Don't run ocp_viewer",
        )
        ap.add_argument(
            "--no-browser",
            "-B",
            dest="open_viewer",
            action="store_false",
            help="Don't open browser for ocp_viewer",
        )
        ap.add_argument(
            "--delay",
            "-d",
            dest="delay",
            default=0.5,
            metavar="seconds",
            type=float,
            help=(
                "How long to wait after event before rendering model"
                " (default: %(default)s seconds)"
            ),
        )
        ap.add_argument(
            "--viewer-args",
            "-A",
            dest="ocp_viewer_args",
            default="--theme=dark",
            metavar="args",
            help=(
                "Additional arguments to provide to ocp_viewer"
                " (default: %(default)s)"
            ),
        )
        ap.add_argument(
            "model_name", help="Model name to render when changes detected"
        )
        return ap.parse_args()

    @contextmanager
    def ocp_viewer(self) -> Iterator[None]:
        if not self.args.viewer:
            yield
            return
        try:
            print("Starting OCP viewer")
            url = f"http://localhost:{OCP_VIEWER_PORT}/viewer"
            viewer_process = subprocess.Popen(
                ["python", "-m", "ocp_vscode"]
                + self.args.ocp_viewer_args.split()
            )  # nosec B603
            for _ in range(100):
                try:
                    urlopen(url).read()  # nosec B310
                    break
                except URLError:
                    time.sleep(0.25)
            else:
                raise Exception("OCP viewer communication failed")
            if self.args.open_viewer:
                webbrowser.open_new_tab(url)
                time.sleep(0.5)
            yield
        finally:
            print("Stopping OCP viewer")
            viewer_process.kill()
            viewer_process.communicate()

    @contextmanager
    def event_watcher(self) -> Iterator[None]:
        try:
            print("Starting event watcher")
            event_handler = self.EventHandler(
                callback=self.runner.trigger, patterns=["*.py"]
            )
            observer = Observer()
            observer.schedule(event_handler, ".", recursive=True)
            observer.start()
            yield
        finally:
            print("Stopping event watcher")
            self.runner.stop()
            observer.stop()
            observer.join()
            self.runner.join()

    @cached_property
    def condition(self) -> Condition:
        return Condition()

    @cached_property
    def runner(self) -> Runner:
        _runner = Runner(
            run_callback=self.run_callback,
            condition=self.condition,
            delay=self.args.delay,
            daemon=True,
        )
        _runner.start()
        return _runner

    def run_callback(self) -> None:
        try:
            mn = __name__.split(".")[0]
            current_module = sys.modules[mn]
            for mod in [
                p
                for m, p in sys.modules.items()
                if m == mn or m.startswith(f"{mn}.")
            ]:
                try:
                    reload(mod)
                except ModuleNotFoundError:
                    traceback.print_exc()
            if not hasattr(current_module.models, self.args.model_name):
                import_module(
                    f"{current_module.models.__name__}.{self.args.model_name}"
                )
            model_class = getattr(
                current_module.models, self.args.model_name
            ).Model()
            assert isinstance(model_class, BaseModel)
            model = model_class.model
            print(model.show_topology())
            show(model, axes=True, axes0=True, transparent=False)
            model_class.export_to_step()
        except KeyboardInterrupt:
            raise
        except Exception:
            traceback.print_exc()
        print("")


class Runner(Thread):
    def __init__(
        self,
        condition: Condition,
        run_callback: Callable[[], None],
        delay: float = 0.5,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.condition = condition
        self.run_callback = run_callback
        self.delay = delay
        self.next_execute_time: float = 0
        self.exit_event = Event()

    def run(self) -> None:
        with self.condition:
            self.run_callback()
            while True:
                timeout = None
                tm = time.time()
                if tm < self.next_execute_time:
                    timeout = self.next_execute_time - tm
                notified = self.condition.wait(timeout=timeout)
                if self.exit_event.is_set():
                    break
                if not notified:
                    # Timeout expired
                    self.run_callback()

    def stop(self) -> None:
        self.exit_event.set()
        with self.condition:
            self.condition.notify_all()

    def trigger(self) -> None:
        with self.condition:
            self.next_execute_time = time.time() + self.delay
            self.condition.notify()


def main() -> None:
    Watcher()()


if __name__ == "__main__":
    main()
