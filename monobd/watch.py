from __future__ import annotations

import sys
import time
import traceback
from argparse import ArgumentParser, Namespace
from functools import cached_property
from importlib import reload
from threading import Condition, Event, Thread
from typing import Any, Callable

from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    PatternMatchingEventHandler,
)
from watchdog.observers import Observer

import monobd


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
        event_handler = self.EventHandler(
            callback=self.runner.trigger, patterns=["*.py"]
        )
        observer = Observer()
        observer.schedule(event_handler, ".", recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1000)
        except KeyboardInterrupt:
            print("")
        finally:
            self.runner.stop()
            observer.stop()
            observer.join()
            self.runner.join()

    @cached_property
    def args(self) -> Namespace:
        ap = ArgumentParser("Model automatic renderer for development")
        ap.add_argument(
            "--delay",
            "-d",
            dest="delay",
            default=0.5,
            metavar="seconds",
            type=float,
            help=(
                "How long to wait after event before running target"
                " (default: %(default)s seconds)"
            ),
        )
        ap.add_argument(
            "target", help="Module to execute when changes detected"
        )
        return ap.parse_args()

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
        mn = __name__.split(".")[0]
        for mod in [
            p
            for m, p in sys.modules.items()
            if m == mn or m.startswith(f"{mn}.")
        ]:
            reload(mod)
        try:
            getattr(monobd, self.args.target).main()
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
