from typing import Callable, Self
from collections.abc import Iterator

import traceback

type Builder = Iterator[Build]

class Build:
    type Dependency = Callable[[], bool]

    def __init__(self, func: Callable = lambda: None):
        self.creation_traceback = traceback.extract_stack()
        self.creation_traceback.pop(len(self.creation_traceback)-1)

        self.func = func
        self.condition = lambda: True

        self.depends = []

        self.finished = []

    @classmethod
    def target(cls, *builders: Builder) -> Self:
        return cls().on_finish_builder(*builders)

    def add_condition(self, condition: Callable[[], bool]) -> Self:
        self.condition = lambda old=self.condition: old() and condition()
        return self

    def depends_on(self, dependency: Dependency) -> Self:
        self.depends.append(dependency)
        return self

    def on_finish(self, finish: Callable[[], Self | None]) -> Self:
        self.finished.append(finish)
        return self

    def on_finish_builder(self, *builders: Builder) -> Self:
        last = self
        for builder in builders:
            for build in builder:
                last.finished.append(lambda ret=build: ret)
                last = build
        return self

from . import build
from . import conditions
from . import executor
from . import cc

from .executor import execute
