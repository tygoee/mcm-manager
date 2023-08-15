from os import path, get_terminal_size
from tqdm import tqdm
from typing import Any
from urllib import parse, request, error
from install.headers import headers
from install.url_generator import generate_url


def prepare_media(total_size: int, install_path: str, mods: list[dict[str, Any]], resourcepacks: list[dict[str, Any]]) -> int:
    """Get the file size and check media validity while listing all media"""

    def check_media_validity(media_list: list[dict[str, Any]], media_type: str) -> None:
        """Check for the modpack file validity"""
        for media in media_list:
            for key in ['type', 'slug', 'name']:
                if key not in media:
                    raise KeyError(
                        f"The '{key}' key should be specified in the following {media_type}: {media}.")
            if media['type'] not in ['cf', 'mr', 'pm', 'url']:
                raise KeyError(
                    f"The type '{media['type']}' does not exist: {media}.")

    def get_headers(media: dict[str, Any], total_size: int) -> int:
        """Recieve the content-length headers"""
        try:
            size = int(request.urlopen(
                url).headers.get('content-length', 0))
        except error.HTTPError:
            # When returning an HTTP error, try again
            # while mimicking a common browser user agent
            size = int(request.urlopen(request.Request(
                url, headers=headers)).headers.get('content-length', 0))

        media['_'] += (size,)
        total_size += size

        return total_size

    if len(mods) != 0:
        check_media_validity(mods, 'mod')

        # List the installed mods and prepare the modpack
        print("\nMods:")

        for mod in mods:
            # Add the corresponding url to mod['_']
            url, mod['_'] = generate_url(mod, install_path, 'mods')

            # Append the mod size to the total size and save it in mod['_']
            total_size = get_headers(mod, total_size)

            # Print the mod name
            print(f"  {mod['slug']} ({parse.unquote(mod['name'])})")

    if len(resourcepacks) != 0:
        check_media_validity(resourcepacks, 'resourcepack')

        # List the installed resourcepacks and prepare the resourcepack
        print("\nResourcepacks:")

        for resourcepack in resourcepacks:
            # Add the corresponding url to mod['_']
            url, resourcepack['_'] = generate_url(
                resourcepack, install_path, 'resourcepacks')

            # Append the mod size to the total size and save it in mod['_']
            total_size = get_headers(resourcepack, total_size)

            # Print the mod name
            print(
                f"  {resourcepack['slug']} ({parse.unquote(resourcepack['name'])})")

    # At the end, return the total mods size
    return total_size


def download_media(url: str, fname: str, size: int, skipped_files: int, outer_bar: tqdm, inner_bar: tqdm) -> int:  # type: ignore
    if not path.isfile(fname):
        description = f"Installing {parse.unquote(path.basename(fname))}..."
        if len(description) > get_terminal_size().columns:
            description = description[:get_terminal_size().columns]

        outer_bar.set_description_str(description)
        try:
            with request.urlopen(url) as resp:
                with open(fname, 'wb') as mod_file:
                    while True:
                        data = resp.read(1024)
                        if not data:
                            break
                        size = mod_file.write(data)
                        inner_bar.update(size)
                        inner_bar.refresh()
        except error.HTTPError:
            with request.urlopen(request.Request(url, headers=headers)) as resp:
                with open(fname, 'wb') as mod_file:
                    while True:
                        data = resp.read(1024)
                        if not data:
                            break
                        size = mod_file.write(data)
                        inner_bar.update(size)
                        inner_bar.refresh()

    else:
        skipped_files += 1

        description = f"{parse.unquote(path.basename(fname))} is already installed, skipping..."
        if len(description) > get_terminal_size().columns:
            description = description[:get_terminal_size().columns]

        outer_bar.set_description_str(description)

        inner_bar.update(size)
        inner_bar.refresh()

    # Return the amount of skipped files
    return skipped_files
