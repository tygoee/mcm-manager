from typing import (
    Literal, TypedDict, TypeVar,
    Generic, NotRequired, Optional
)

# --- install/filesize.py --- #
SizeSystem = list[tuple[int, str | tuple[str, str]]]


# --- install --- #
Client = Literal['client']
Server = Literal['server']
Side = Literal['client', 'server']

_T = TypeVar("_T", bound=Literal['cf', 'pm', 'mr', 'url'])


class Minecraft(TypedDict):
    version: str
    modloader: str


class Info(TypedDict, total=False):
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
    info: NotRequired[Info]

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
    minecraft: Minecraft
    mods: Media
    resourcepacks: Media
    shaderpacks: Media


# --- modloaders.py --- #
class _OSDict(TypedDict):
    name: Literal["windows", "linux", "osx"]  # NotRequired
    arch: NotRequired[Literal["x86"]]


class Library(TypedDict):
    "All libraries of the media"
    path: str
    sha1: str
    size: int
    url: str


class _Rules(TypedDict):
    action: Literal["allow", "disallow"]
    features: NotRequired[dict[str, bool]]
    os: _OSDict  # NotRequired


class OSLibrary(Library, _Rules):
    "All libraries of the media for a specific os"


Libraries = dict[str, Library | OSLibrary]


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


class _JavaLibrary(TypedDict):
    downloads: _Download
    name: str
    rules: NotRequired[list[_Rules]]


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


class JavaJson(TypedDict):
    arguments: _Arguments
    id: str
    libraries: list[_JavaLibrary]
    logging: _Logging
    mainClass: str
    releaseTime: str
    time: str
    type: str


class MinecraftJson(JavaJson):
    "Minecraft version_manifest.json file"
    assetIndex: _AssetIndex
    assets: str
    complianceLevel: int
    downloads: _Downloads
    javaVersion: _JavaVersion
    minimumLauncherVersion: int


class VersionJson(JavaJson):
    "Minecraft version.json file"
    inheritsFrom: str


# -- Install profile -- #
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
    libraries: list[_JavaLibrary]
    icon: str
    json: str
    logo: str
    mirrorList: str
    welcome: str
