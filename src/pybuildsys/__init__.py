from dataclasses import dataclass
import functools

from typing import Callable, Iterator, ParamSpec, Self

import os
import subprocess

P = ParamSpec("P")


class RetryException(Exception):
    """
    Raise this to restart the target at a later time
    """

    def __init__(self) -> None:
        super().__init__()

@dataclass
class Special:
    pass

type Build = Callable
type Target = Iterator[Build | Target | Special]

@dataclass
class Later(Special):
    """
    Yield this to continue the target at a later time
    """

    pass

@dataclass
class WrapTarget(Later):
    wrapper: Callable[[Target], Target]

@dataclass
class Barrier(Later):
    """
    Yield this to wait until there are no more targets in the queue
    """

    pass

class DependsOn(WrapTarget):
    def __init__(self, depends_on: Callable[[], bool]) -> None:
        def wrapper(target: Target):
            while not depends_on():
                yield Later()

            yield from target

        super().__init__(wrapper)

def target():
    def annotator(func: Callable[P, Target]):
        @functools.wraps(func)
        def inner(*args: P.args, **kwargs: P.kwargs) -> Target:
            while True:
                try:
                    yield from func(*args, **kwargs)
                except RetryException:
                    continue
                
                break

        return inner

    return annotator

def shell(path, *args, env=os.environ, silent=False) -> Build:
    def build():
        if not silent:
            print(path, *args)

        subprocess.run([path, *args]).check_returncode()

    return build

from . import conditions
from . import executor
from . import cc
from . import stage

from .executor import execute
