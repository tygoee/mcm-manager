from os import path
from typing import Any, TypeAlias
from urllib import parse

Media: TypeAlias = dict[str, Any]


def generate_media_url(media: Media, install_path: str, folder: str) -> tuple[str, tuple[str, str]]:
    """Generate an url to download"""

    match media['type']:
        case 'cf':
            url = "https://mediafilez.forgecdn.net/files/" + \
                f"{int(str(media['id'])[:4])}/{int(str(media['id'])[4:])}/{media['name']}"
        case 'mr':
            url = "https://cdn-raw.modrinth.com/data/" + \
                f"{media['id'][:8]}/versions/{media['id'][8:]}/{media['name']}"
        case 'pm':
            url = "https://static.planetminecraft.com/files/resource_media/" + \
                f"{media['media']}/{media['name']}"
        case 'url':
            url: str = media['link']
        case _:
            raise KeyError(
                f"The mod type '{media['type']}' does not exist.")

    return url, (url, path.join(install_path, folder, parse.unquote(media['name'])))
