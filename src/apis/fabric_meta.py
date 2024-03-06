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
from typing import Literal, Optional, overload
from urllib import request
from http.client import HTTPResponse
from ..typings import (
    # Versions
    GameVersion, IntermediaryVersion,
    YarnVersion, AllVersions,

    # Loader
    FabricVersionJson, LoaderJson, InstallerLibrary, LibraryList
)

from ..common.maven_coords import maven_parse


def api_url(url: str, *paths: str) -> str:
    if not url[-1] == '/':
        url += '/'

    return url + '/'.join(paths)


# Types are not defined because these endpoints are unused
class versions:
    def __init__(self, game_version: Optional[str] = None) -> None:
        """
        Creates a fabric-meta versions object.

        :param game_version: The minecraft version to select
        """

        self.game_version = game_version
        self._base_url = "https://meta.fabricmc.net/v2/versions/"

    def all(self) -> AllVersions:
        "Full database, includes all the data. Warning: large JSON."

        url = api_url(self._base_url)
        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())

    def yarn(self) -> list[YarnVersion]:
        """
        Lists all of the yarn versions, stable is based on the Minecraft version.
        When `game_version` is specified, it lists all of the yarn versions for the provided game version.
        """

        if self.game_version is None:
            url = api_url(self._base_url, 'yarn')
        else:
            url = api_url(self._base_url, 'yarn', self.game_version)

        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())

    def intermediary(self) -> list[IntermediaryVersion]:
        """
        Lists all of the intermediary versions, stable is based of the Minecraft version.
        When `game_version` is specified, it only lists the provided game version.
        """

        if self.game_version is None:
            url = api_url(self._base_url, 'intermediary')
        else:
            url = api_url(self._base_url, 'intermediary', self.game_version)

        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())


class game:
    def __init__(self) -> None:
        "Creates a fabric-meta game versions object"

        self._base_url = "https://meta.fabricmc.net/v2/versions/game/"

    def all(self) -> list[GameVersion]:
        "Lists all of the supported game versions."

        url = api_url(self._base_url)
        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())

    def yarn(self) -> list[GameVersion]:
        "Lists all of the compatible game versions for yarn."

        url = api_url(self._base_url, 'yarn')
        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())

    def intermediary(self) -> list[GameVersion]:
        "Lists all of the compatible game versions for intermediary."

        url = api_url(self._base_url, 'intermediary')
        response: HTTPResponse = request.urlopen(url)

        return loads(response.read())


class loader:
    @overload
    def __init__(
        self, game_version: str,
        loader_version: Optional[str] = None
    ) -> None:
        """
        Creates a fabric-meta loader object.

        To get the result, use `loader.result`.
        For other values, use `loader`, `intermediary` and `launcher_meta`

        :param game_version: The minecraft version to select
        :param loader_version: The fabric loader version to select
        """

    @overload
    def __init__(
        self, game_version: Optional[str] = None
    ) -> None:
        """
        Creates a fabric-meta loader object.

        To get the result, use `loader.result`.
        For other values, use `loader`, `intermediary` and `launcher_meta`

        :param game_version: The minecraft version to select
        """

    def __init__(
        self, game_version: Optional[str] = None,
        loader_version: Optional[str] = None
    ) -> None:
        """
        Creates a fabric-meta loader object.

        To get the result, use `loader.result`.
        For other values, use `loader`, `intermediary` and `launcher_meta`

        :param game_version: The minecraft version to select
        :param loader_version: The fabric loader version to select
        """

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

        response: HTTPResponse = request.urlopen(api_url(self._url))
        self.result: LoaderJson = loads(response.read().decode('utf-8'))

        self.loader = self.result['loader']
        self.intermediary = self.result['intermediary']
        self.launcher_meta = self.result['launcherMeta']

    def libraries(
        self, launcher_dir: str,
        side: Optional[Literal['client', 'server']] = None,
        extra: list[InstallerLibrary] = []
    ) -> LibraryList:
        "Lists all of the libraries"
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
        "Returns the JSON file that should be used in the standard Minecraft launcher."

        if not self._complete:
            raise ValueError(
                "Cannot fetch profile json if 'game_version' "
                "and 'loader_version' isn't specified"
            )

        url = api_url(self._url, 'profile', 'json')
        response: HTTPResponse = request.urlopen(url)

        return loads(response.read().decode('utf-8'))

    def profile_zip(self) -> bytes:
        "Downloads a zip file with the launcher's profile json, and the dummy jar. To be extracted into .minecraft/versions"
        if not self._complete:
            raise ValueError(
                "Cannot fetch profile zip if 'game_version' "
                "and 'loader_version' isn't specified"
            )

        url = api_url(self._url, 'profile', 'zip')
        response: HTTPResponse = request.urlopen(url)

        return response.read()

    def server_json(self) -> bytes:
        "Returns the JSON file in format of the launcher JSON, but with the server's main class."
        if not self._complete:
            raise ValueError(
                "Cannot fetch server json if 'game_version' "
                "and 'loader_version' isn't specified"
            )

        url = api_url(self._url, 'server', 'json')
        response: HTTPResponse = request.urlopen(url)

        return response.read()
