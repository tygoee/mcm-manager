from os import path, get_terminal_size
from tqdm import tqdm
from typing import Any
from urllib import parse, request, error
from install.headers import headers


def prepare_mods(total_size: int, install_path: str, mod_list: list[dict[str, Any]]) -> int:
    """Get the `content-length` headers while listing all mods"""

    # Check for the json file validity
    for mod in mod_list:
        for key in ['type', 'slug', 'name']:
            if key not in mod:
                raise KeyError(
                    f"The '{key}' key should be specified in the following mod: {mod}.")
        if mod['type'] not in ['cf', 'mr', 'url']:
            raise KeyError(
                f"The mod type '{mod['type']}' does not exist: {mod}.")

    # List the installed mods and prepare the modpack
    print("\nMods:")

    for mod in mod_list:
        # Add the corresponding url to mod['_']
        match mod['type']:
            case 'cf':
                url = f"https://mediafilez.forgecdn.net/files/{int(str(mod['id'])[:4])}/{int(str(mod['id'])[4:])}/{mod['name']}"
                mod['_'] = (url, path.join(install_path,
                                           'mods', parse.unquote(mod['name'])))
            case 'mr':
                url = f"https://cdn-raw.modrinth.com/data/{mod['id'][:8]}/versions/{mod['id'][8:]}/{mod['name']}"
                mod['_'] = (url, path.join(install_path,
                                           'mods', parse.unquote(mod['name'])))
            case 'url':
                url = mod['link']
                mod['_'] = (url, path.join(install_path,
                                           'mods', parse.unquote(mod['name'])))
            case _:
                raise KeyError(
                    f"The mod type '{mod['type']}' does not exist.")

        # Recieve the content-length headers
        try:
            size = int(request.urlopen(
                url).headers.get('content-length', 0))
            mod['_'] += (size,)
            total_size += size
        except error.HTTPError:
            # When returning an HTTP error, try again
            # while mimicking a common browser user agent
            size = int(request.urlopen(request.Request(url,
                                                       headers=headers)).headers.get('content-length', 0))
            mod['_'] += (size,)
            total_size += size

        # Print the mod name
        print(f"  {mod['slug']} ({parse.unquote(mod['name'])})")

    # At the end, return the total mods size
    return total_size


def download_mods(url: str, fname: str, size: int, skipped_mods: int, outer_bar: tqdm, inner_bar: tqdm):  # type: ignore
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
        skipped_mods += 1

        description = f"{parse.unquote(path.basename(fname))} is already installed, skipping..."
        if len(description) > get_terminal_size().columns:
            description = description[:get_terminal_size().columns]

        outer_bar.set_description_str(description)

        inner_bar.update(size)
        inner_bar.refresh()

    # Return the amount of skipped mods
    return skipped_mods
