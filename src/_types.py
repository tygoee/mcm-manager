"Private type classes, exports are in _types"

from typing import Literal, TypedDict, NotRequired

SizeSystem = list[tuple[int, str | tuple[str, str]]]
Side = Literal['client', 'server']


class Minecraft(TypedDict):
    version: str
    modloader: str


class __Media(TypedDict):
    "Private values for Media"
    sides: list[Literal['client', 'server']]
    slug: str
    name: str
    info: NotRequired[dict[str, str]]

    # Download info: url, path, size
    _dl: tuple[str, str, int]


class CFMedia(__Media):
    "Media for CurseForge"
    type: Literal['cf']
    id: int


class PMMedia(__Media):
    "Media for CurseForge"
    type: Literal['pm']
    media: str


class MRMedia(__Media):
    "Media for CurseForge"
    type: Literal['mr']
    id: str


class URLMedia(__Media):
    "Media for CurseForge"
    type: Literal['url']
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


class Answers(TypedDict):
    manifest_file: str
    install_path: str
    side: Literal['client', 'server']
    install_modloader: bool
    launcher_path: str
