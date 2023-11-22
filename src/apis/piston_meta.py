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

from http.client import HTTPResponse
from json import loads
from urllib import request


from ..typings import MinecraftJson

version_manifest_v2 = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


def get_minecraft_json(mc_version: str) -> MinecraftJson:
    """Get the minecraft json from a minecraft"""
    res: HTTPResponse = request.urlopen(version_manifest_v2)
    for item in loads(res.read().decode('utf-8'))['versions']:
        if item['id'] == mc_version:
            res = request.urlopen(item['url'])
            return loads(res.read().decode('utf-8'))

    raise KeyError("Couldn't find minecraft version in version manifest")
