from dataclasses import dataclass
from typing import Callable, Iterator, Self

import traceback

import queue
import threading

from . import Barrier, Build, Later, RetryException, Target, WrapTarget

def execute(target: Target, jobs=1) -> None:
    @dataclass
    class TargetEntry:
        target: Target
        parent: Self | None = None

        child_count: int = 0

        def change_child_count(self, amount: int):
            self.child_count += amount
            if self.parent:
                self.parent.change_child_count(amount)

    target_queue = queue.Queue()

    root_entry = TargetEntry(target)
    target_queue.put(root_entry)

    stop = False
    exception: Exception | None = None

    def build_target(entry: TargetEntry):
        target = entry.target

        def barrier_target():
            while entry.child_count > 0:
                yield Later()

            yield from target

        for build in target:
            if callable(build):
                build()
            elif isinstance(build, Iterator):
                entry.change_child_count(1)
                target_queue.put(TargetEntry(build, parent=entry))
            elif isinstance(build, Later):
                if isinstance(build, WrapTarget):
                    entry.target = build.wrapper(target)
                elif isinstance(build, Barrier):
                    entry.target = barrier_target()

                target_queue.put(entry)
                return

        entry.change_child_count(-1)

    def build_thread_func():
        nonlocal exception

        while not exception:
            try:
                target = target_queue.get(timeout=0.1)

                try:
                    build_target(target)
                except Exception as e:
                    exception = e
                finally:
                    target_queue.task_done()
            except queue.Empty:
                if stop:
                    break

    build_threads = []
    for _ in range(jobs):
        build_threads.append(threading.Thread(target=build_thread_func))

    try:
        for thread in build_threads:
            thread.start()
    finally:
        stop = True
        for thread in build_threads:
            if thread.is_alive():
                thread.join()

    if exception:
        raise exception

