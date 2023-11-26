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

from json import loads
from typing import Literal, Optional, overload, TYPE_CHECKING
from urllib import request

if TYPE_CHECKING:
    from http.client import HTTPResponse

from ..typings import FabricVersionJson, LoaderJson, InstallerLibrary, LibraryList

from ..common.maven_coords import maven_parse


def api_url(url: str, *paths: str) -> str:
    if not url[-1] == '/':
        url += '/'

    return url + '/'.join(paths)


class loader:
    @overload
    def __init__(
        self, game_version: str,
        loader_version: Optional[str] = None
    ) -> None: ...

    @overload
    def __init__(
        self, game_version: Optional[str] = None
    ) -> None: ...

    def __init__(
        self, game_version: Optional[str] = None,
        loader_version: Optional[str] = None
    ) -> None:
        """Create an fabric-meta loader object"""

        self.game_version = game_version
        self.loader_version = loader_version
        self._complete = False

        base_url = "https://meta.fabricmc.net/v2/versions/loader/"

        if game_version is None and loader_version is None:
            self._url = base_url
        elif game_version is not None and loader_version is None:
            self._url = api_url(base_url, game_version)
        elif game_version is not None and loader_version is not None:
            self._complete = True
            self._url = api_url(base_url, game_version, loader_version)
        else:
            raise ValueError(
                "'loader_version' may not be passed when 'game_version' is None"
            )

        response: 'HTTPResponse' = request.urlopen(api_url(self._url))
        self.result: LoaderJson = loads(response.read().decode('utf-8'))

    def libraries(
        self, launcher_dir: str,
        side: Optional[Literal['client', 'server']] = None,
        extra: list[InstallerLibrary] = []
    ) -> LibraryList:
        """Get all the libraries with a filename"""
        libs: LibraryList = []

        for lib_type in self.result['launcherMeta']['libraries'].keys():
            if (lib_type not in ('client', 'common', 'server') or not
                    (side in (None, lib_type) or lib_type == 'common')):
                continue

            for lib in self.result['launcherMeta']['libraries'][lib_type] + extra:
                maven = maven_parse(lib['name'])
                libs.append({
                    'name': lib['name'],
                    'url': maven.to_url(lib['url']),
                    'file': maven.to_file(launcher_dir, 'libraries')
                })

        return libs

    def profile_json(self) -> FabricVersionJson:
        if not self._complete:
            raise ValueError(
                "Cannot fetch profile zip if 'game_version' "
                "and 'loader_version' isn't specified"
            )

        url = api_url(self._url, 'profile', 'json')
        response: 'HTTPResponse' = request.urlopen(url)

        return loads(response.read().decode('utf-8'))

    def profile_zip(self) -> bytes:
        if not self._complete:
            raise ValueError(
                "Cannot fetch profile zip if 'game_version' "
                "and 'loader_version' isn't specified"
            )

        url = api_url(self._url, 'profile', 'zip')
        response: 'HTTPResponse' = request.urlopen(url)

        return response.read()
