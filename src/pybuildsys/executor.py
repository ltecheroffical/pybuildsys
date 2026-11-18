from typing import Callable


import traceback

import threading

from . import Build, Builder

def execute(builder: Builder, jobs=1) -> None:
    builds: list[Build] = []
    stop = False

    def build_command(command: Build):
        for dep in command.depends:
            if not dep():
                builds.append(command)
                return

        try:
            if command.condition():
                command.func()

            for finish in command.finished:
                build = finish()
                if isinstance(build, Build):
                    builds.append(build)

        except Exception as e:
            build_traceback = "".join(traceback.format_list(command.creation_traceback))
            e.add_note(f"""
The exception above was directly caused by a build:

Traceback (most recent call last):
{build_traceback}""")
            raise

    def build_thread_func():
        nonlocal stop

        while True:
            if len(builds) <= 0:
                if stop:
                    break

                continue

            build = builds.pop(0)
            try:
                build_command(build)
            except Exception:
                stop = True
                builds.clear()

    build_threads = []
    for _ in range(jobs):
        build_threads.append(threading.Thread(target=build_thread_func))

    try:
        for thread in build_threads:
            thread.start()

        for build in builder:
            builds.append(build)
    finally:
        stop = True
        for thread in build_threads:
            if thread.is_alive():
                thread.join()

