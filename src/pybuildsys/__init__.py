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
    def target(cls, builder: Builder) -> Self:
        return cls().on_finish_builder(builder)

    def and_condition(self, condition: Callable[[], bool]) -> Self:
        self.condition = lambda old=self.condition: old() and condition()
        return self

    def or_condition(self, condition: Callable[[], bool]) -> Self:
        self.condition = lambda old=self.condition: old() or condition()
        return self

    def depends_on(self, dependency: Dependency) -> Self:
        self.depends.append(dependency)
        return self

    def on_finish(self, finish: Callable[[], Self | None]) -> Self:
        self.finished.append(finish)
        return self

    def on_finish_builder(self, builder: Builder) -> Self:
        for build in builder:
            self.finished.append(lambda ret=build: ret)

        return self

from . import build
from . import conditions
from . import executor
from . import cc
from . import stage

from .executor import execute
