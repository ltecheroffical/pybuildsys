import os
import sys

import subprocess
import threading

from . import Build

from typing import Self
from dataclasses import dataclass

def async_print(*args, **kwargs):
    threading.Thread(target=print, args=args, kwargs=kwargs).start()

def shell(path, *args, env=os.environ, silent=False) -> Build:
    def builder():
        if not silent:
            async_print(path, *args)

        subprocess.run([path, *args]).check_returncode()

    return Build(builder)
