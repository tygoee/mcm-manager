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

from os import path, mkdir
from json import dump
from .vars import install_dir, launcher_dir

# Create the install dir
if not path.isdir(install_dir):
    mkdir(install_dir)

# Create the launcher dir and example-manifest.json
if not path.isdir(launcher_dir):
    mkdir(launcher_dir)

launcher_profiles = {
    "profiles": {},
    "settings": {
        "crashAssistance": True,
        "enableAdvanced": False,
        "enableAnalytics": True,
        "enableHistorical": False,
        "enableReleases": True,
        "enableSnapshots": False,
        "keepLauncherOpen": False,
        "profileSorting": "ByLastPlayed",
        "showGameLog": False,
        "showMenu": False,
        "soundOn": False
    },
    "version": 3
}

with open(path.join(launcher_dir, 'launcher_profiles.json'), 'w') as fp:
    dump(launcher_profiles, fp, indent=4)
