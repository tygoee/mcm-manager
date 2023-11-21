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

from os import mkdir, path
from shutil import copy
from ..config import INSTDIR, LAUNDIR, LAUNPROF, TMPDIR


def maketemp():
    """Make a temp directory"""

    if not path.isdir(TMPDIR):
        mkdir(TMPDIR)


def setup_dirs() -> None:
    """Setup necesarry directories"""

    # Make a temp directory
    maketemp()

    # Create the install dir
    if not path.isdir(INSTDIR):
        mkdir(INSTDIR)

    # Create the launcher dir and example-manifest.json
    if not path.isdir(LAUNDIR):
        mkdir(LAUNDIR)

    # Copy the launcher profiles
    copy(LAUNPROF, path.join(LAUNDIR, 'launcher_profiles.json'))
