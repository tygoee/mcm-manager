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

from os import path, makedirs
from install import filesize, media, modloaders

from install._types import URLMedia, MediaList, Side

app_root = path.join(path.dirname(path.realpath(__file__)), '..')


def install(manifest_file: str,
            install_path: str = path.join(app_root, 'share', '.minecraft'),
            side: Side = 'client',
            install_modloader: bool = True,
            launcher_path: str = modloaders.MINECRAFT_DIR,
            confirm: bool = True) -> None:
    """
    Install a list of mods, resourcepacks, shaderpacks and config files. Arguments:

    :param manifest_file: This should be a path to a manifest file. \
                          For the file structure, look at the README
    :param install_path: The base path everything should be installed to
    :param side: 'client' or 'server': The side to be installed
    :param install_modloader: If you want to install the modloader
    :param launcher_path: The path of your launcher directory
    :param confirm: If the user should confirm the download
    """

    # Import the manifest file
    manifest = media.prepare.load_manifest(manifest_file)

    # List the modpack info
    modpack_version: str = manifest['minecraft']['version']
    modloader: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[0]
    modloader_version: str = manifest['minecraft']['modloader'].split(
        '-', maxsplit=1)[1]

    print(f"Modpack version: {modpack_version}\n" +
          f"Mod loader: {modloader}\n"
          f"Mod loader version: {modloader_version}")

    mods: MediaList = manifest.get('mods', [])
    resourcepacks: MediaList = manifest.get('resourcepacks', [])
    shaderpacks: MediaList = manifest.get('shaderpacks', [])

    total_size = media.prepare(install_path, side, manifest)

    # Give warnings for external sources
    external_media: list[URLMedia] = [_media for _media in [mod for mod in mods] +
                                      [resourcepack for resourcepack in resourcepacks] +
                                      [shaderpack for shaderpack in shaderpacks]
                                      if _media['type'] == 'url']
    if len(external_media) != 0:
        print("\nWARNING! Some mods/resourcepacks/shaderpacks are from" +
              " external sources and could harm your system:")
        for _media in external_media:
            print(
                f"  {_media['slug']} ({_media['name']}): {_media['url']}")

    # Print the mod info
    print(
        f"\n{len(mods)} mods, {len(resourcepacks)} " +
        f"recourcepacks, {len(shaderpacks)} shaderpacks\n" +
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}")

    # Ask for confirmation if confirm is True and install all modpacks
    if confirm:
        try:
            if input("Continue? (Y/n) ").lower() not in ['y', '']:
                print("Cancelling...\n")
                exit()
        except KeyboardInterrupt:
            print(end='\n')
            exit(130)
    else:
        print("Continue (Y/n) ")

    # Download and install the modloader
    if install_modloader:
        match modloader:
            case 'forge':
                if side == 'client':
                    modloaders.forge(modpack_version, modloader_version,
                                     side, install_path, launcher_path)
                if side == 'server':
                    modloaders.forge(modpack_version, modloader_version,
                                     side, install_path)
            case _:
                print("Installing this modloader isn't supported yet.")

    # Download all files
    media.download_files(total_size, install_path, side, manifest)


def main():
    from typing import TypedDict, Literal

    Answers = TypedDict("Answers", {
        "manifest_file": str,
        "install_path": str,
        "side": Literal['client', 'server'],
        "install_modloader": bool,
        "launcher_path": str
    })

    current_dir = path.dirname(path.realpath(__file__))

    # Define all questions
    questions = [
        "Manifest file location (default: example-manifest.json): ",
        "Install location (default: share/gamedir): ",
        "Install side (client/server, default: client): ",
        "Do you want to install the modloader? (Y/n, default: n): ",
        f"Launcher location (default: {modloaders.MINECRAFT_DIR}): "
    ]

    # Ask all questions
    try:
        answers: Answers = {
            "manifest_file": input(questions[0]),
            "install_path": input(questions[1]),
            "side": 'server' if input(questions[2]) == 'server' else 'client',
            "install_modloader": (inst_modl := True if input(questions[3]).lower() == 'y' else False),
            "launcher_path": input(questions[4]) if inst_modl else ''
        }
    except KeyboardInterrupt:
        print(end='\n')
        exit(130)

    # Set the defaults
    defaults = {
        "launcher_path": modloaders.MINECRAFT_DIR,
        "manifest_file": path.join(current_dir, '..', 'share', 'modpacks', 'example-manifest.json'),
        "install_path": path.join(current_dir, '..', 'share', 'gamedir')
    }

    for default in defaults:
        if answers[default] == '':
            answers[default] = defaults[default]

    if not path.isdir(answers["install_path"]):
        makedirs(answers["install_path"])

    print('\n', end='')

    install(**answers)


if __name__ == '__main__':
    main()
