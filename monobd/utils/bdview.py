from __future__ import annotations

import subprocess  # nosec B404
import sys
import time
import traceback
import webbrowser
from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from functools import cached_property
from importlib import reload
from pathlib import Path
from threading import Condition, Event, Thread
from types import ModuleType
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import urlopen

import psutil
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

from ..common import Model


@dataclass
class Watcher:
    modules: OrderedDict[str, ModuleType] = field(default_factory=OrderedDict)

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
                time.sleep(1)
                self.runner.trigger()
                while True:
                    time.sleep(1000)
            except KeyboardInterrupt:
                print("")

    @cached_property
    def args(self) -> Namespace:
        ap = ArgumentParser(
            description="Model automatic renderer for development"
        )
        ap.add_argument(
            "--no-viewer",
            "-N",
            dest="viewer",
            action="store_false",
            help="Don't run ocp_viewer",
        )
        ap.add_argument(
            "--restart-viewer",
            "-R",
            dest="restart_viewer",
            action="store_true",
            help="Restart ocp_viewer if it is already running",
        )
        ap.add_argument(
            "--stop-viewer",
            "-S",
            dest="stop_viewer_on_exit",
            action="store_true",
            help="Stop ocp_viewer on exit",
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
            "-D",
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
            default="--theme=dark --reset_camera=keep",
            metavar="args",
            help=(
                "Additional arguments to provide to ocp_viewer"
                " (default: %(default)s)"
            ),
        )
        ap.add_argument(
            "-d",
            "--destination",
            dest="dest",
            type=Path,
            metavar="dir",
            default=None,
            help=(
                "Export rendered models to this directory on render"
                " (default: no models exported)"
            ),
        )
        ap.add_argument(
            "model_name", help="Model name to render when changes detected"
        )
        ap.add_argument(
            "variant_name", nargs="?", default="", help="Model variant name"
        )
        return ap.parse_args()

    @cached_property
    def ocp_viewer_process(self) -> psutil.Process | None:
        return next(
            iter(
                psutil.Process(c.pid)
                for c in psutil.net_connections()
                if c.laddr
                and c.laddr.port == OCP_VIEWER_PORT
                and c.pid
                and c.status.lower() == "listen"
            ),
            None,
        )

    @contextmanager
    def ocp_viewer(self) -> Iterator[None]:
        if not self.args.viewer:
            yield
            return
        url = f"http://localhost:{OCP_VIEWER_PORT}/viewer"
        if self.ocp_viewer_process:
            if not self.args.restart_viewer:
                print(f"OCP viewer is already running: {url}")
                yield
                return
            print(
                "Stopping already running OCP viewer"
                f" (PID {self.ocp_viewer_process.pid})"
            )
            self.ocp_viewer_process.terminate()
            psutil.wait_procs([self.ocp_viewer_process], timeout=2)
            del self.ocp_viewer_process
        print("Starting OCP viewer")
        try:
            subprocess.Popen(
                ["python", "-m", "ocp_vscode"]
                + self.args.ocp_viewer_args.split(),
                start_new_session=True,
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
            if self.args.stop_viewer_on_exit and self.ocp_viewer_process:
                print("Stopping OCP viewer")
                self.ocp_viewer_process.terminate()
                psutil.wait_procs([self.ocp_viewer_process], timeout=2)

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
            with suppress(RuntimeError):
                observer.join()
            with suppress(RuntimeError):
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

    def reload_modules(self) -> None:
        mn = __name__.split(".")[0]
        for m, p in sys.modules.items():
            if not (m == mn or m.startswith(f"{mn}.")):
                continue
            if m not in self.modules:
                self.modules[m] = p
        print("Reloading imports")
        for mod in self.modules.values():
            try:
                reload(mod)
            except ModuleNotFoundError:
                traceback.print_exc()

    def run_callback(self) -> None:
        try:
            self.reload_modules()
            print("Rendering model")
            model = Model._models[self.args.model_name].variant(
                self.args.variant_name
            )
            print(model.assembly.show_topology())
            show(model.assembly, axes=True, axes0=True, transparent=False)
            if self.args.dest:
                model.export(self.args.dest, step=True, stl=False)
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
