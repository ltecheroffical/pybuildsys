import os
from typing import Callable

def changed(output: str, *producers: str) -> bool:
    if not os.path.exists(output):
        return True

    for producer in producers:
        if not os.path.exists(producer):
            return True

        if os.path.getmtime(producer) > os.path.getmtime(output):
            return True

    return False
