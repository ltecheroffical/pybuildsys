import os
import glob
import subprocess

from typing import Callable, Self
from dataclasses import dataclass, field

from pybuildsys import Build
from pybuildsys.build import shell
from pybuildsys.conditions import changed

def c_compiler_vendor(compiler: str) -> str | None:
    result = subprocess.run(
        [compiler, "--version"],
        capture_output=True, text=True
    )
    output = (result.stdout + result.stderr).lower()

    if "clang" in output:
        return "clang"
    elif "gcc" in output or "g++" in output:
        return "gcc"

    return None

def c_linker_vendor(linker: str) -> str | None:
    vendor = c_compiler_vendor(linker)
    if vendor:
        return vendor

    result = subprocess.run(
        [linker, "--version"],
        capture_output=True, text=True
    )
    output = (result.stdout + result.stderr).lower()

    if "gnu" in output:
        return "gnu"

    return None

def c_archiver_vendor(archiver: str) -> str | None:
    result = subprocess.run(
        [archiver, "--version"],
        capture_output=True, text=True
    )
    output = (result.stdout + result.stderr).lower()

    if "gnu" in output:
        return "gnu"

    return None

def c_changed(output: str, *sources: str) -> Callable[[], bool]:
    def func():
        deps = []
        dep_file = os.path.splitext(output)[0] + ".d"

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

@dataclass
class CFlags:
    common: bool = True
    strict: bool = False

    std: str | None = "c99"

    include: list[str] = field(default_factory=list)

    manual: list[str] = field(default_factory=list)

    def compute(self, compiler: str, output: str, *sources: str) -> list[str]:
        flags: list[str] = list(self.manual)
        vendor = c_compiler_vendor(compiler)

        if vendor == "clang" or vendor == "gcc":
            flags.append("-c")

            if self.common:
                flags += ["-Wall", "-Wextra", "-MMD"]

            if self.strict:
                flags += ["-Werror", "-pedantic-errors"]

            if self.std:
                flags.append(f"-std={self.std}")

            for include in self.include:
                flags.append(f"-I{include}")

        return flags + ["-o", output, *sources]

@dataclass
class LDFlags:
    static: bool = False

    libs: list[str] = field(default_factory=list)
    static_libs: list[str] = field(default_factory=list)
    libc: bool = True

    build_shared: bool = False

    manual: list[str] = field(default_factory=list)

    def compute(self, linker: str, output: str, *objects: str) -> list[str]:
        flags: list[str] = list(self.manual)
        libs: list[str] = list(self.static_libs)
        vendor = c_linker_vendor(linker)

        if vendor == "gcc" or vendor == "clang":
            if self.static:
                flags.append("-static")

            if self.build_shared:
                flags.append("-shared")

            if not self.libc:
                flags.append("-nostdlib")

            for lib in self.libs:
                libs.append(f"-l{lib}")

            if self.libc:
                libs.append("-lm")

        return flags + ["-o", output, *objects, *self.static_libs, *libs]

@dataclass
class ARFlags:
    common: bool = True

    manual: list[str] = field(default_factory=list)

    def compute(self, linker: str, output: str, *objects: str) -> list[str]:
        flags: list[str] = list(self.manual)
        vendor = c_archiver_vendor(linker)

        if vendor == "gnu":
            if self.common:
                flags.append("rcs")

        return flags + [output, *objects]


@dataclass
class Toolchain:
    cc: str = "gcc"
    cxx: str = "g++"
    ld: str = "gcc"
    ar: str = "ar"

    cflags: CFlags = field(default_factory=CFlags)
    cxxflags: CFlags = field(default_factory=CFlags)
    ldflags: LDFlags = field(default_factory=LDFlags)
    arflags: ARFlags = field(default_factory=ARFlags)

    def with_c_prefix(self, prefix: str) -> Self:
        self.cc = prefix + self.cc
        self.cxx = prefix + self.cxx

        return self

def cc(toolchain: Toolchain, output: str, *sources: str) -> Build:
    return (
        shell(toolchain.cc, *toolchain.cflags.compute(toolchain.cc, output, *sources))
            .add_condition(c_changed(output, *sources))
    )

def cxx(toolchain: Toolchain, output: str, *sources: str) -> Build:
    return (
        shell(toolchain.cc, *toolchain.cxxflags.compute(toolchain.cxx, output, *sources))
            .add_condition(c_changed(output, *sources))
    )

def ld(toolchain: Toolchain, output: str, *objects: str) -> Build:
    return (
        shell(toolchain.ld, *toolchain.ldflags.compute(toolchain.ld, output, *objects))
            .add_condition(changed(output, *objects))
    )

def ar(toolchain: Toolchain, output: str, *objects: str) -> Build:
    return (
        shell(toolchain.ar, *toolchain.arflags.compute(toolchain.ar, output, *objects))
            .add_condition(changed(output, *objects))
    )
