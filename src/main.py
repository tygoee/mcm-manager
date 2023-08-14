from json import load
from os import path, get_terminal_size, mkdir

from typing import Any
from urllib import parse, request, error
from tqdm import tqdm
import filesize


def prepare_mods(total_size: int, install_path: str, mods: list[dict[str, Any]]) -> int:
    """Get the `content-length` headers while listing all mods"""

    # Check for the json file validity
    for mod in mods:
        for key in ['type', 'slug', 'name']:
            if key not in mod:
                raise KeyError(
                    f"The '{key}' key should be specified in the following mod: {mod}.")
        if mod['type'] not in ['cf', 'mr', 'url']:
            raise KeyError(
                f"The mod type '{mod['type']}' does not exist: {mod}.")

    # List the installed mods and prepare the modpack
    print("\nMods:")

    for mod in mods:
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
            total_size += int(request.urlopen(
                url).headers.get('content-length', 0))
        except error.HTTPError:
            # When returning an HTTP error, try again
            # while mimicking a common browser user agent
            total_size += int(request.urlopen(request.Request(url,
                              headers=headers)).headers.get('content-length', 0))

        # Print the mod name
        print(f"  {mod['slug']} ({parse.unquote(mod['name'])})")

    # At the end, return the total mods size
    return total_size


def download_files(total_size: int, install_path: str, mods: list[dict[str, Any]]):
    """Download all files with a tqdm loading bar"""
    if not path.isdir(path.join(install_path, 'mods')):
        mkdir(path.join(install_path, 'mods'))

    print('\033[?25l')  # Hide the cursor
    skipped_mods = 0

    with tqdm(
        total=total_size,
        position=1,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        bar_format='{desc}'
    ) as outer_bar:
        for url, fname in (inner_bar := tqdm(
                [mod['_']
                    for mod in mods],
                position=0,
                unit='B',
                unit_scale=True,
                total=total_size,
                unit_divisor=1024,
                bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                leave=False)):
            if not path.isfile(fname):
                try:
                    outer_bar.set_description_str(
                        f"Installing {parse.unquote(path.basename(fname))}...")
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
                outer_bar.set_description_str(
                    f"{parse.unquote(path.basename(fname))} is already installed, skipping...")

                # Get the content-length headers (again) to update the bar
                try:
                    inner_bar.update(int(request.urlopen(
                        url).headers.get('content-length', 0)))
                except error.HTTPError:
                    # When returning an HTTP error, try again
                    # while mimicking a common browser user agent
                    inner_bar.update(int(request.urlopen(request.Request(
                        url, headers=headers)).headers.get('content-length', 0)))

                inner_bar.refresh()

    print('\033[2A\033[?25h')  # Go two lines back and show cursor

    # Make a new bar that directly updates to 100% as
    # the last one will dissapear after the loop is done
    if total_size != 0:
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}'
        ) as bar:
            bar.update(total_size)
    else:
        with tqdm(
            total=1,
            unit='it',
            bar_format='{percentage:3.0f}%|{bar}| 0.00/0.00'
        ) as bar:
            bar.update(1)

    print(' ' * (get_terminal_size().columns) + '\r', end='')
    print(
        f"Skipped {skipped_mods}/{len(mods)} mods that were already installed" if skipped_mods != 0 else '\n')


def install(manifest_file: str, install_path: str = '', confirm: bool = True) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a
    manifest file. The file structure:

    ```json
    {
        "minecraft": {
            "version": "(version)",
            "modloader": "(modloader)-(modloader version)"
        },
        "mods": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ]
    }
    ```

    :param install_path: The base path everything should be installed to
    :param confirm: If the user should confirm the download
    """

    # Import the manifest file
    with open(manifest_file) as json_file:
        manifest: dict[str, Any] = load(json_file)

    # Check for validity
    if manifest.get('minecraft', None) is None:
        raise KeyError("The modpack must include a 'minecraft' section.")
    if manifest['minecraft'].get('version', None) is None:
        raise KeyError(
            "The 'minecraft' section must include the minecraft version.")
    if manifest['minecraft'].get('modloader', None) is None or \
            '-' not in manifest['minecraft']['modloader']:
        raise KeyError(
            "The 'minecraft' section must include the modloader " +
            "and version in this format: 'modloader-x.x.x'")

    # List the modpack info
    modpack_version: str = manifest['minecraft']['version']
    modloader: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[0]
    modloader_version: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[1]

    print(f"Modpack version: {modpack_version}\n" +
          f"Mod loader: {modloader}\n"
          f"Mod loader version: {modloader_version}")

    # The headers to mimic a common browser user agent
    global headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    total_size = 0

    if manifest.get('mods', None) is not None:
        total_size = prepare_mods(total_size, install_path, manifest['mods'])

    print(
        f"\n{len(manifest.get('mods', []))} mods, 0 recourcepacks, 0 shaderpacks\n" +
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}")  # type: ignore

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm == True:
        if input("Continue? (Y/n) ").lower() not in ['y', '']:
            print("Cancelling...\n")
            exit()
    else:
        print("Continue (Y/n) ")

    # Download all files
    download_files(total_size, install_path, manifest.get('mods', []))
