import os
import sys

import subprocess

from . import Build

def shell(path, *args, env=os.environ, silent=False) -> Build:
    def builder():
        if not silent:
            print(path, *args)

        subprocess.run([path, *args]).check_returncode()

    return Build(builder)
