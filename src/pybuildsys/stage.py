from typing import Callable

from . import Build, DependsOn

class Stage:
    def __init__(self) -> None:
        self.completed = 0
        self.stage = 0

    def next(self) -> Callable[[], bool]:
        func = lambda stage = self.stage: self.completed >= stage
        self.stage += 1
        return func

    def complete(self) -> None:
        self.completed += 1
