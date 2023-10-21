"Private type classes, exports are in _types"

from typing import Literal, TypedDict


class Minecraft(TypedDict):
    version: str
    modloader: str


class __NtMedia(TypedDict):
    "Non-total values for Media"
    sides: list[Literal['client', 'server']]
    slug: str
    name: str

    # Download info: url, path, size
    _dl: tuple[str, str, int]


class __PvtMedia(__NtMedia, total=False):
    "Private Media class for Medias that may not exist"
    info: dict[str, str]


class CFMedia(__PvtMedia):
    "Media for CurseForge"
    type: Literal['cf']
    id: int


class PMMedia(__PvtMedia):
    "Media for CurseForge"
    type: Literal['pm']
    media: str


class MRMedia(__PvtMedia):
    "Media for CurseForge"
    type: Literal['mr']
    id: str


class URLMedia(__PvtMedia):
    "Media for CurseForge"
    type: Literal['url']
    link: str


# Dictionary with info about a mod, resourcepack or shaderpack
Media = CFMedia | PMMedia | MRMedia | URLMedia


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
