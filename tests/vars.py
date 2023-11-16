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
from typing import Callable, Any
from os import path, walk, remove
from shutil import rmtree


def quiet(func: Callable[..., Any]) -> Callable[..., Any]:
    "A simple decorator function that supresses stdout"
    def wrapper(*args: Any, **kwargs: Any):
        with redirect_stdout(None):
            result = func(*args, **kwargs)
        return result
    return wrapper


def empty_dir(*directories: str):
    for directory in directories:
        for root, dirs, files in walk(directory):
            for f in files:
                remove(path.join(root, f))
            for d in dirs:
                rmtree(path.join(root, d))


launcher_dir = path.realpath(
    path.join(path.dirname(path.realpath(__file__)), '.minecraft'))

install_dir = path.realpath(path.join(path.dirname(
    path.realpath(__file__)), 'gamedir'))

current_dir = path.dirname(path.realpath(__file__))
