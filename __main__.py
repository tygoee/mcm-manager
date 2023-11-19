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

from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, fields
from os import path, makedirs
from typing import Any, Literal, Optional, TypedDict, TypeVar

from src.install import filesize, media, modloaders
from src.install._types import URLMedia, MediaList, Side


class Options(TypedDict):
    manifest_file: str
    install_path: str
    side: Side
    install_modloader: bool
    launcher_path: str
    confirm: bool


@dataclass(init=False)
class Args:
    # Positional arguments
    pos: Literal[False] | str

    # Options
    y: bool            # confirm installation
    o: bool            # skip modloader install
    m: Optional[str]   # manifest
    i: Optional[str]   # install path
    s: Optional[Side]  # side
    l: Optional[str]   # launcher path

    def __init__(self, **kwargs: Any) -> None:
        """Ignore non-existent names"""
        names = set(f.name for f in fields(self))
        for k, v in kwargs.items():
            if k in names:
                setattr(self, k, v)


current_dir = path.dirname(path.realpath(__file__))
app_root = path.join(path.dirname(path.realpath(__file__)), '..')
default_args = Args(**vars(Namespace(
    pos=False, y=False, m=None, i=None, s=None, l=None, o=False)))


def install(
    manifest_file: str,
    install_path: str = path.join(app_root, 'share', '.minecraft'),
    side: Side = 'client',
    install_modloader: bool = True,
    launcher_path: str = modloaders.MINECRAFT_DIR,
    confirm: bool = True
) -> None:
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
        print("\nWARNING! Some mods/resourcepacks/shaderpacks are from"
              " external sources and could harm your system:")
        for _media in external_media:
            print(f"  {_media['slug']} ({_media['name']}): {_media['url']}")

    # Print the mod info
    print(
        f"\n{len(mods)} mods, {len(resourcepacks)} recourcepacks, {len(shaderpacks)} shaderpacks\n"
        f"Total file size: {filesize.size(total_size, system=filesize.alternative)}"
    )

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
                elif side == 'server':
                    modloaders.forge(modpack_version, modloader_version,
                                     side, install_path)
            case _:
                print("WARNING: Couldn't install modloader because it isn't supported.")

    # Download all files
    media.download_files(total_size, install_path, side, manifest)


_T = TypeVar("_T")


def ask(arg: _T | None, question: _T) -> _T | str:
    return input(question) if arg is None else arg


def ask_yes(arg: _T, question: _T) -> bool:
    return input(question).lower() == 'y' if arg else arg


def cli(args: Args = default_args):
    """Ask questions and execute `install()` with the answers"""

    # Define all questions
    questions = [
        "Manifest file location (default: example-manifest.json): ",
        "Install location (default: share/gamedir): ",
        "Install side (client/server, default: client): ",
        "Do you want to install the modloader? (y/N, default: n): ",
        f"Launcher location (default: {modloaders.MINECRAFT_DIR}): "
    ]

    # Ask all questions
    try:
        answers: Options = {
            "manifest_file": ask(args.m, questions[0]),
            "install_path": ask(args.i, questions[1]),
            "side": 'server' if ask(args.s, questions[2]) == 'server' else 'client',
            "install_modloader": (inst_modl := ask_yes(not args.o, questions[3])),
            "launcher_path": ask(args.l, questions[4]) if inst_modl else '',
            "confirm": not args.y
        }
    except KeyboardInterrupt:
        print(end='\n')
        exit(130)

    # Set the defaults
    defaults = {
        "manifest_file": path.join(current_dir, '..', 'share', 'modpacks', 'example-manifest.json'),
        "install_path": path.join(current_dir, '..', 'share', 'gamedir'),
        "launcher_path": modloaders.MINECRAFT_DIR
    }

    # Cycle through them and apply
    for default in defaults:
        if answers[default] == '':
            answers[default] = defaults[default]

    # Make the install directory if it's nonexistent
    if not path.isdir(answers["install_path"]):
        makedirs(answers["install_path"])

    print('\n', end='')

    # Install
    install(**answers)


def main():
    # Make a parser
    parser = ArgumentParser(
        prog="mcm-manager",
        description="Minecraft Modpack Manager"
    )

    # Add positional arguments
    parser.add_argument(
        'pos', nargs='?', default=False, metavar='cli',
        help='use a cli interface to install a modloader'
    )

    parser.add_argument(
        'install', nargs='?', default=False,
        help='install a package directly'
    )

    # Define optional arguments
    optional_args: list[tuple[tuple[str, ...], str, str] | tuple[tuple[str, ...], str]] = [
        (('-y', '--yes'), "continue installation without confirmation"),
        (('-m',), 'MANIFEST', "specify the manifest file to load"),
        (('-i',), 'INSTPATH', "specify the path where it will be installed"),
        (('-s',), 'SIDE', "specify the side to be installed (client or server)"),
        (('-l',), 'LAUNCHERPATH', "specify the path of the launcher"),
        (('-o',), "skip the installation of the modloader"),
    ]

    # Add optional arguments
    for arg in optional_args:
        if len(arg) == 3:
            parser.add_argument(
                *arg[0], metavar=arg[1],
                help=arg[2]
            )
        else:
            parser.add_argument(
                *arg[0], action='store_true',
                dest=arg[0][0][1], help=arg[1]
            )

    # Get the args and execute the right function
    args = Args(**vars(parser.parse_args()))

    if args.s not in ('client', 'server') and args.s is not None:
        raise TypeError("side has to be either 'client', 'server' or None.")

    match args.pos:
        case 'cli':
            cli(args)
        case 'install':
            # Set the defaults
            options: Options = {
                "manifest_file": args.m or path.join(current_dir, '..', 'share',
                                                     'modpacks', 'example-manifest.json'),
                "install_path": args.i or path.join(current_dir, '..', 'share', 'gamedir'),
                "side": 'server' if args.s == 'server' else 'client',
                "install_modloader": (inst_modl := not args.o),
                "launcher_path": args.l if args.l is not None and inst_modl else modloaders.MINECRAFT_DIR,
                "confirm": not args.y
            }

            install(**options)

        case _:
            # TODO else, execute the gui (not finished)
            raise NotImplementedError(
                "Calling without any (or invalid) positional arguments will open a gui, "
                "but this is not implemented yet.\n" + parser.format_usage()
            )


if __name__ == '__main__':
    main()
