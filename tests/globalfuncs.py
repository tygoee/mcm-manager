# MCM-Manager: Minecraft Modpack Manager
# Copyright (C) 2023  Tygo Everts
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from contextlib import redirect_stdout
from typing import Any, Callable
from os import path, remove, walk
from shutil import rmtree

from .config import TMPDIR


def empty_dir(directory: str):
    "Empty a directory"
    for root, dirs, files in walk(directory):
        for f in files:
            remove(path.join(root, f))
        for d in dirs:
            rmtree(path.join(root, d))


def quiet(func: Callable[..., Any]) -> Callable[..., Any]:
    "A simple decorator function that supresses stdout"
    def wrapper(*args: Any, **kwargs: Any):
        with redirect_stdout(None):
            result = func(*args, **kwargs)
        return result
    return wrapper


def cleanup(func: Callable[..., Any]) -> Callable[..., Any]:
    "A function that removes the temp directory after completion"
    def wrapper(*args: Any, **kwargs: Any):
        func(*args, **kwargs)
        empty_dir(TMPDIR)
    return wrapper
