from typing import Callable

import traceback

import queue
import threading

from . import Build, Builder

def execute(builder: Builder, jobs=1) -> None:
    builds = queue.Queue()

    stop = False
    exception: Exception | None = None

    def build_command(command: Build):
        for dep in command.depends:
            if not dep():
                builds.put(command)
                return

        try:
            if command.condition():
                command.func()

            for finish in command.finished:
                build = finish()
                if isinstance(build, Build):
                    builds.put(build)

        except Exception as e:
            build_traceback = "".join(traceback.format_list(command.creation_traceback))
            e.add_note(f"""
The exception above was directly caused by a build:

Traceback (most recent call last):
{build_traceback}""")
            raise

    def build_thread_func():
        nonlocal exception

        while not exception:
            try:
                build = builds.get(timeout=0.1)
                try:
                    build_command(build)
                except Exception as e:
                    exception = e
                finally:
                    builds.task_done()
            except queue.Empty:
                if stop:
                    break

    build_threads = []
    for _ in range(jobs):
        build_threads.append(threading.Thread(target=build_thread_func))

    try:
        for thread in build_threads:
            thread.start()

        for build in builder:
            builds.put(build)
    finally:
        stop = True
        for thread in build_threads:
            if thread.is_alive():
                thread.join()

    if exception:
        raise exception

