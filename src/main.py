from json import load
from os import path, get_terminal_size, mkdir
from tqdm import tqdm
from typing import Any, TypeAlias
from install import filesize, media

MediaList: TypeAlias = list[dict[str, Any]]
Media: TypeAlias = dict[str, Any]


def download_files(total_size: int, install_path: str, mods: MediaList, resourcepacks: MediaList):
    """Download all files with a tqdm loading bar"""
    if not path.isdir(path.join(install_path, 'mods')):
        mkdir(path.join(install_path, 'mods'))
    if not path.isdir(path.join(install_path, 'resourcepacks')):
        mkdir(path.join(install_path, 'resourcepacks'))

    print('\033[?25l')  # Hide the cursor
    skipped_files = 0

    with tqdm(
        total=total_size,
        position=1,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        bar_format='{desc}'
    ) as outer_bar:
        for url, fname, size in (inner_bar := tqdm(
            [mod['_'] for mod in mods] +
            [resourcepack['_'] for resourcepack in resourcepacks],
            position=0,
            unit='B',
            unit_scale=True,
            total=total_size,
            unit_divisor=1024,
            bar_format='{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}',
                leave=False)):
            skipped_files = media.download_media(  # type: ignore
                url, fname, size, skipped_files, outer_bar, inner_bar)

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
        f"Skipped {skipped_files}/{len(mods) + len(resourcepacks)} files that were already installed" if skipped_files != 0 else '')


def install(manifest_file: str, install_path: str = path.dirname(path.realpath(__file__)), confirm: bool = True) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a manifest file. The file structure:

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
        ],
        "resourcepacks": [
            {
                "type": "(type)",
                "slug": "(slug)",
                "name": "(filename)"
            }
        ],
        "shaderpacks": [
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
        manifest: Media = load(json_file)

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

    total_size = 0

    total_size = media.prepare_media(
        total_size, install_path, manifest.get('mods', []), manifest.get('resourcepacks', []))

    print(
        f"\n{len(manifest.get('mods', []))} mods, {len(manifest.get('resourcepacks', []))} recourcepacks, 0 shaderpacks\n" +
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}")  # type: ignore

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm == True:
        if input("Continue? (Y/n) ").lower() not in ['y', '']:
            print("Cancelling...\n")
            exit()
    else:
        print("Continue (Y/n) ")

    # Download all files
    download_files(total_size, install_path, manifest.get(
        'mods', []), manifest.get('resourcepacks', []))


if __name__ == '__main__':
    if (mcm_location := input("Manifest file location (default: example-manifest.json): ")) == '':
        mcm_location = path.join(path.dirname(
            path.realpath(__file__)), 'example-manifest.json')

    if (install_location := input("Install location (default: current directory): ")) == '':
        install(mcm_location)
    else:
        install(mcm_location, install_location)
