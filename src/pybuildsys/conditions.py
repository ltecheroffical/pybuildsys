import os
from typing import Callable

def changed(output: str, *producers: str) -> Callable[[], bool]:
    def func():
        if not os.path.exists(output):
            return True

        for producer in producers:
            if os.path.getmtime(producer) > os.path.getmtime(output):
                return True

        return False

    return func

def c_changed(output: str, *sources: str) -> Callable[[], bool]:
    def func():
        deps = []
        dep_file = output + ".d"

        if os.path.exists(dep_file):
            result = ""
            with open(dep_file, "r") as f:
                result = f.readline()[:-1]
                while result[len(result)-1] == "\\":
                    result = result[:-1] + f.readline().rstrip("\n")

            deps = result.split(":")[1].split()

        if changed(output, *(list(sources) + deps))():
            return True

        return False

    return func
