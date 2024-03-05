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

from typing import (
    Literal, TypedDict, TypeVar,
    Generic, NotRequired, Optional
)

# ============================ #
#      install/filesize.py     #
# ============================ #
SizeSystem = list[tuple[int, str | tuple[str, str]]]


# ============================ #
#            install/          #
# ============================ #
Client = Literal['client']
Server = Literal['server']
Side = Literal['client', 'server']

_T = TypeVar("_T", bound=Literal['cf', 'pm', 'mr', 'url'])


class _Minecraft(TypedDict):
    version: str
    modloader: str


class _Info(TypedDict, total=False):
    "Dictionary with info about media"
    title: str
    icon: str
    description: str


class _Media(Generic[_T], TypedDict):
    "Private values for Media"
    type: _T
    slug: str
    name: str
    sides: list[Literal['client', 'server']]
    info: NotRequired[_Info]

    # Download info: url, path, size
    _dl: NotRequired[tuple[str, str, int]]


class CFMedia(_Media[Literal['cf']]):
    "Media for CurseForge"
    id: int


class PMMedia(_Media[Literal['pm']]):
    "Media for PlanetMinecraft"
    media: str


class MRMedia(_Media[Literal['mr']]):
    "Media for Modrinth"
    id: str


class URLMedia(_Media[Literal['url']]):
    "Media for custom urls"
    url: str


# Dictionary with info about a mod, resourcepack or shaderpack
Media = CFMedia | PMMedia | MRMedia | URLMedia
MediaList = list[Media]


class Manifest(TypedDict):
    "All information of the modpack"
    minecraft: _Minecraft
    mods: MediaList
    resourcepacks: MediaList
    shaderpacks: MediaList


# ============================ #
#     install/modloaders.py    #
# ============================ #
Modloader = Literal['forge', 'fabric'] | str


class _Settings(TypedDict):
    enableAnalytics: bool
    enableAdvanced: bool
    keepLauncherOpen: bool
    soundOn: bool
    showMenu: bool
    enableSnapshots: bool
    enableHistorical: bool
    enableReleases: bool
    profileSorting: str
    showGameLog: bool
    crashAssistance: bool


class _Profile(TypedDict, total=False):
    gameDir: str
    lastUsed: str
    lastVersionId: str
    created: str
    name: str
    icon: str
    type: Literal['latest-release', 'latest-snapshot', 'custom']


class LauncherProfiles(TypedDict):
    settings: _Settings
    profiles: dict[str, _Profile]
    version: int


# ========= #
#   Forge   #
# ========= #


# Libraries
class _OSDict(TypedDict):
    name: Literal["windows", "linux", "osx"]  # NotRequired
    arch: NotRequired[Literal["x86"]]


class ForgeLibrary(TypedDict):
    "A forge library"
    path: str
    sha1: str
    size: int
    url: str


class _Rules(TypedDict):
    action: Literal["allow", "disallow"]
    features: NotRequired[dict[str, bool]]
    os: _OSDict  # NotRequired


class OSLibrary(ForgeLibrary, _Rules):
    "A library for a specific OS"
    ...


Libraries = dict[str, ForgeLibrary | OSLibrary]


# Forge minecraft and version json
class _Arg(TypedDict):
    rules: list[_Rules]
    value: str | list[str]


class _Arguments(TypedDict):
    game: list[str | _Arg]
    jvm: list[str | _Arg]


class _AssetIndex(TypedDict):
    id: str
    sha1: str
    size: int
    totalSize: int
    url: str


class _SimpleDownload(TypedDict):
    sha1: str
    size: int
    url: str


class _Downloads(TypedDict):
    client: _SimpleDownload
    client_mappings: _SimpleDownload
    server: _SimpleDownload
    server_mappings: _SimpleDownload


class _JavaVersion(TypedDict):
    component: str
    majorVersion: int


class _Artifact(TypedDict):
    path: str
    sha1: str
    size: int
    url: str


class _Download(TypedDict):
    artifact: _Artifact


class _File(TypedDict):
    id: str
    sha1: str
    size: int
    url: str


class _LoggingClient(TypedDict):
    argument: str
    file: _File
    type: str


class _Logging(TypedDict):
    client: _LoggingClient


_L = TypeVar('_L')


class _JavaJson(TypedDict, Generic[_L]):
    arguments: _Arguments
    id: str
    libraries: list[_L]
    logging: _Logging
    mainClass: str
    releaseTime: str
    time: str
    type: str


class _ForgeLibrary(TypedDict):
    downloads: _Download
    name: str
    rules: NotRequired[list[_Rules]]


class MinecraftJson(_JavaJson[_ForgeLibrary]):
    "Minecraft version_manifest.json file"
    assetIndex: _AssetIndex
    assets: str
    complianceLevel: int
    downloads: _Downloads
    javaVersion: _JavaVersion
    minimumLauncherVersion: int


class ForgeVersionJson(_JavaJson[_ForgeLibrary]):
    "Forge's minecraft version.json file"
    inheritsFrom: str


# Install profile
class _Data(TypedDict):
    client: str
    server: str


class _Processor(TypedDict):
    sides: list[Side]
    jar: str
    classpath: list[str]
    args: list[str]
    outputs: NotRequired[dict[str, str]]


class InstallProfile(TypedDict):
    spec: int
    profile: str
    version: str
    path: Optional[str]
    serverJarPath: str
    data: dict[str, _Data]
    processors: list[_Processor]
    libraries: list[_ForgeLibrary]
    icon: str
    json: str
    logo: str
    mirrorList: str
    welcome: str


# ========== #
#   Fabric   #
# ========== #


# Versions
class GameVersion(TypedDict):
    version: str
    stable: bool


class IntermediaryVersion(GameVersion):
    maven: str


class LoaderVersion(IntermediaryVersion):
    separator: str
    build: int


class InstallerVersion(IntermediaryVersion):
    url: str


class YarnVersion(LoaderVersion):
    gameVersion: str


class AllVersions(TypedDict):
    game: list[GameVersion]
    mappings: list[YarnVersion]
    intermediary: list[IntermediaryVersion]
    loader: list[LoaderVersion]
    installer: ...


# Loader
class InstallerLibrary(TypedDict):
    name: str
    url: str


class LoaderLibraries(TypedDict):
    client: list[InstallerLibrary]
    common: list[InstallerLibrary]
    server: list[InstallerLibrary]


class MainClass(TypedDict):
    client: str
    server: str


class LauncherMeta(TypedDict):
    version: int
    libraries: LoaderLibraries
    mainClass: MainClass


class LoaderJson(TypedDict):
    "Information about the fabric loader"
    loader: LoaderVersion
    intermediary: IntermediaryVersion
    launcherMeta: LauncherMeta


class FabricLibrary(InstallerLibrary):
    "A fabric library"
    file: str


LibraryList = list[FabricLibrary]


# Fabric version json
class FabricVersionJson(_JavaJson[InstallerLibrary]):
    "Fabric's minecraft version.json file"
    inheritsFrom: str
