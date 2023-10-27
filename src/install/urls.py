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

from os import path
from urllib import parse

from ._types import Media


def media_url(media: Media, install_path: str, folder: str) -> tuple[str, tuple[str, str]]:
    """Generate an url to download"""

    match media['type']:
        case 'cf':
            url = "https://mediafilez.forgecdn.net/files/" + \
                f"{int(str(media['id'])[:4])}/" +  \
                f"{int(str(media['id'])[4:])}/{media['name']}"
        case 'mr':
            url = "https://cdn-raw.modrinth.com/data/" + \
                f"{media['id'][:8]}/versions/{media['id'][8:]}/{media['name']}"
        case 'pm':
            url = "https://static.planetminecraft.com/files/resource_media/" + \
                f"{media['media']}/{media['name']}"
        case 'url':
            url: str = media['url']

    return url, (url, path.join(install_path, folder, parse.unquote(media['name'])))


class forge:
    @staticmethod
    def forge_installer_url(mc_version: str, forge_version: str) -> str:
        return "https://maven.minecraftforge.net/net/minecraftforge/forge/" + \
            f"{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-installer.jar"

    @staticmethod
    def version_manifest_v2() -> str:
        return "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"


class fabric:
    @staticmethod
    def api_url(*paths: str) -> str:
        return "https://meta.fabricmc.net/" + '/'.join(paths)
